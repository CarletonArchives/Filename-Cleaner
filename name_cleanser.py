"""
name_cleanser takes a database and strips the file names of illegal characters, replacing them with an underscore
legal characters are alphanumerical characters and underscores
If a file is renamed it gets stored in BAGNAME\\data\\meta\\renames.csv 
There will be one renames file for every directory in the directory that is originally passed to the program
If the program cannot rename a file for some reason it will store the file path in an errors.csv file in the top directory 

Code by Caitlin Donahue
    caitlindonahue95@gmail.com
based off of data_accessioner.py by Liam Everett
    liam.m.everett@gmail.compile
    that was edited by Sahree Kasper
    sahreek@gmail.com

June 2015
"""
import os
import sys
import datetime
import time
import csv
import re
import shutil
import ast
import codecs
import cStringIO
import errno

class NameCleanser:
    def __init__(self, settings_file, path_arg):
        #files to ignore (taken from settings file)
        self.excludes = []
        #where to store the files(taken from settings file)
        self.storage_location_name = ""
        #The amount of time to sleep when retrying an error
        #.5 is the default, but it is rewritten by the setting file
        #1 is fairly safe, can change depending on the system
        self.error_check_time = .5
        #initialize the cleanse settings using a file
        self.initialize_cleanse_settings(settings_file)
        #Characters that are allowed in file names
        self.safe_chars ="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_."
        #The location of the topmost directory
        self.top_directory = path_arg
        # entries will be of the form {new_name:old_name}
        self.original_file_names = {} 
        #Sets the current date for use in the rename file
        self.now = datetime.datetime.now()
        #a counter for how many files have been looked at (just extra info for testing)
        self.datestamp = str(self.now.year) + "_" + str(self.now.month) + "_" + str(self.now.day)
        self.filenumber = 0
        #counter for the number of errors
        self.errornum = 0
        #keeps track of the current depth in the bags
        self.current_depth = 0
        #Keeps track of which bag we are in for purposes of placing the rename file
        #is updated in iterate_through_drectory
        self.current_bag = self.top_directory
        #the relative path to rename files
        renames_path = os.path.join("data","meta")

    def initialize_cleanse_settings(self, settings_file):
        """ Pulls settings for rename from settings_file """
        path_to_renames = []
        with open(settings_file) as f:
            f_content = [line.rstrip() for line in f]
            parse_state = "none"
            for i in range(len(f_content)):
                line = f_content[i]
                #no parse state yet
                #excludes is the files that are excluded from being checked
                #time is the sleep time in the error check
                if parse_state == "none":
                    if line == "EXCLUDES:":
                        parse_state = "excludes"
                    elif line == "ERROR_CHECK_TIME:":
                        parse_state = "time"
                    elif line == "RELATIVE_PATH_TO_RENAMES:":
                        parse_state = "renames"
                elif parse_state == "excludes":
                    if line != "":
                        self.excludes.append(line)
                    elif line == "ERROR_CHECK_TIME:":
                        parse_state = "time"
                    elif line == "RELATIVE_PATH_TO_RENAMES:":
                        parese_state = "renames"
                    else:
                        parse_state = "none"
                elif parse_state == "time":
                    if line != "":
                        self.error_check_time = float(line)
                    elif line == "EXCLUDES:":
                        parse_state = "excludes"
                    elif line == "RELATIVE_PATH_TO_RENAMES:":
                        parse_state = "renames"
                    else:
                        parse_state = "none" 
                elif parse_state == "renames":
                    if line != "":
                        path_to_renames.append(line)
                    elif line == "ERROR_CHECK_TIME:":
                        parse_state = "time"
                    elif line == "EXCLUDES:":
                        parse_state = "excludes"
                    else:
                        parse_state = "none"
        string_to_renames = ""
        for i in path_to_renames:
            string_to_renames = os.path.join(string_to_renames, i)
        if string_to_renames != "":
            self.renames_path = string_to_renames 

    def is_excluded(self, file_name):
        """ Returns whether or not a file is excluded from the renaming process """
        if file_name in self.excludes:
            return True
        return False

    def check_file_structure(self, path_to_file):
        """ checks if BAGNAME/data/meta exists, creates it if it does not"""
        #this is the structure the data and meta file should be in
        correct_structure = os.path.join(path_to_file, self.renames_path)
        #tries making the file
        try:
            os.makedirs(correct_structure)
        #If an error is raised
        #ignore it if it is telling us the file already exists
        #raise the error if it is related to something else
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
        #return the the file path
        return correct_structure

    def try_rename(self, path_to_file, replacement_path):
        """ tries to rename a file. returns false if it fails and true if it succeeds """
        #tries renaming the file
        try: 
            os.rename(path_to_file, replacement_path)
        except:
            print "Error: Cannot rename file in", os.path.dirname(path_to_file) ,"due to permission errors"
            print "Retrying..."
            if (os.path.exists(replacement_path)):
                #This tests if when trying to rename the file, if there is another file of the same name
                replacement_path = self.handle_repeats(path_to_file, replacement_path)
                print "Testing if multiple files of the same name..."
                try:
                    os.rename(path_to_file, replacement_path)
                except:
                    print "Failed"
                    print "Adding to error file..."
                    #adds the file to the error file
                    self.errornum += 1
                    self.write_error_file(path_to_file)
                    return (False, "")
            else:
                #this checks if there is some sort of error due to os or race conditions
                time.sleep(self.error_check_time)
                try:
                    os.rename(path_to_file, replacement_path)
                except:
                    print "failed"
                    print "adding to error file..."
                    #adds the file to the error file
                    self.errornum += 1
                    self.write_error_file(path_to_file)
                    return (False, "")
            print "Success! File renamed"
            print "------------"
        return (True, replacement_path)

    def handle_repeats(self, path_to_file, replacement_path):
        """ if upon renaming the file name already exists, add numbers to the end of the file name"""
        #If the replacement_path is a directory test file names with increasing numbers until there is an available file name
        if os.path.isdir(replacement_path):
            i = 1
            if not os.path.exists(replacement_path + str(i)):
                replacement_path = replacement_path + str(i)
            while os.path.exists(replacement_path + str(i)):
                i+=1
                if not os.path.exists(replacement_path + str(i)):
                    replacement_path = replacement_path + str(i)
            return replacement_path
        #do the same thing if replacement_path is a file, except place the number before the extension
        else:
            replacement_name = os.path.basename(replacement_path)
            name_list = list(replacement_name)
            num_placement = name_list.index('.')
            i = 1
            while os.path.exists(os.path.join(os.path.dirname(replacement_path), replacement_name)):
                if i == 1:
                    name_list.insert(num_placement, str(i))
                if i != 1:
                    name_list[num_placement] = str(i)
                i += 1
                replacement_name = "".join(name_list)
            return os.path.join(os.path.dirname(replacement_path), replacement_name)

    def iterate_through_dir(self, top_dir, depth):
        """ Goes through folders in the directory, and begins cleansing the names of everything in them 
            This method does not actual;y do the cleansing, but rather iterates through the items in the current
            directory, checking if they can be renamed, then calling the cleanse methods"""
        depth += 1
        #List of the paths that need to be renamed
        path_list = [x for x in os.listdir(ast.literal_eval("u'" + (top_dir.replace("\\", "\\\\")) + "'"))]
        #goes through all of the folders in path_list
        for folder in path_list:
            #gets the path to this folder
            full_folder_path = os.path.join(top_dir, folder)
            #set the global depth to that of the current directory
            self.current_depth = depth
            #the depth should be 1 if top_dir is a bag
            #the depth should be 0 if we are in the top_directory
            if depth == 1:
                self.current_bag = top_dir
            elif depth == 0:
                self.current_bag = full_folder_path
            #if the file is not excluded by the settings file
            if not self.is_excluded(folder):
                #If it is a folder
                if os.path.isdir(full_folder_path):
                    #check if it is a data folder
                    if os.path.basename(full_folder_path) != "meta":
                        #cleanse the folder
                        folder = self.cleanse_dir_name(full_folder_path)
                #If it is a file
                else:
                    #cleanse the file name
                    folder = self.cleanse_file_name(full_folder_path)
            #else:
                #print "not cleansing", folder, "based on cleanse settings \n-----" 

    def cleanse_name(self, name_string, path_to_file):
        """ takes a string that is a name and returns the cleansed version 
        The cleansed version will remove any illegal characters, replacing them with "_", and 
        also replace any periods, excluding the one for the extenson on files"""
        #turns the name into a list that can be iterated through
        replace_list = list(name_string)
        #this is a counter for the number of periods
        periods = 0
        char_index = -1
        period_indeces = []
        # iterate through the characters in the list
        for char in replace_list:
            char_index += 1
            if char == ".":
                #count the number of parenthesis and record their placement
                periods += 1
                period_indeces.append(char_index)
            if char not in self.safe_chars:
                #if the character is not a legal character
                #replace it with an underscore
                replace_list[char_index] = "_"
        if os.path.isdir(path_to_file):
            #if the file is a directory, replace all of the periods
            if periods > 0:
                for i in period_indeces:
                    replace_list[i] = "_"
        else:
            #if the file is not a directory, replace all but the last period
            #this is to keep the extensions properly formatted
            if periods > 1:
                k = 0
                while k < periods - 1:
                    replace_list[period_indeces[k]] = "_"
                    k+=1            
        replace_string = "".join(replace_list)
        replace_string = replace_string.encode("cp850", errors="ignore")              
        return replace_string

    def cleanse_dir_name(self, path_to_dir):
        """ Cleanses the directory name and repeats for any sub-directories """
        #keep track of the number of files renamed for testing purposes
        self.filenumber += 1
        #temp path
        replacement_path = path_to_dir
        #get the file name
        file_name = os.path.basename(path_to_dir)
        #replacement name is a temp variable that has the cleansed version of file_name
        replacement_name = self.cleanse_name(file_name, path_to_dir)
        replacement_name = replacement_name.encode("cp850", errors="ignore")
        renamed = (False, "")
        #try renaming the file
        if replacement_name != file_name:
            replacement_path = os.path.join(os.path.dirname(path_to_dir),replacement_name)
            renamed = self.try_rename(path_to_dir, replacement_path)
        #if the file was successfully renamed 
        if renamed[0]:
            replacement_path = renamed[1]
            replacement_name = os.path.basename(replacement_path)
            file_renamed = []
            #if the file name and replacement name are different, make a list storing
            #the old and new names in the proper format
            if file_name != replacement_name:
                #print os.path.dirname(path_to_dir)+"\\"+replacement_name
                file_renamed.append(self.get_relative_path(path_to_dir))
                file_renamed.append("\\"+replacement_name)
                if path_to_dir == self.current_bag:
                    self.current_bag = replacement_path
            path_to_dir = replacement_path
            #append them to the renames file
            if file_renamed:
                self.write_rename_file(os.path.dirname(path_to_dir),file_renamed)
        self.iterate_through_dir(path_to_dir, self.current_depth)

    def cleanse_file_name(self, path_to_file):
        """ cleanses the file name """
        #keep track of the number of files renamed for testing purposes
        self.filenumber += 1
        #temp path
        replacement_path = path_to_file
        #get the file name
        file_name = os.path.basename(path_to_file)
        #temp name that is the cleansed version of file_name
        replacement_name = self.cleanse_name(file_name, path_to_file)
        replacement_name = replacement_name.encode("cp850", errors="ignore")
        renamed = (False, "")
        #If the replacement name is different than the original name, we have to rename it in the system
        if replacement_name != file_name:
            #create the replacement path
            replacement_path = os.path.join(os.path.dirname(path_to_file), replacement_name)
            #try renaming the file, if it succeeds renamed will equal true
            #if it fails rename will be false
            renamed = self.try_rename(path_to_file, replacement_path)
        #If the file was successfully renamed
        if renamed[0]:
            replacement_path = renamed[1]
            replacement_name = os.path.basename(replacement_path)
            #make a list that contains the hold name and the new name
            file_renamed = []
            if file_name != replacement_name:
                #print os.path.dirname(path_to_file)+"\\"+replacement_name
                file_renamed.append(self.get_relative_path(path_to_file))
                file_renamed.append("\\"+replacement_name)
            #Write this the the renames file
            if file_renamed:
                self.write_rename_file(os.path.dirname(path_to_file), file_renamed)
            path_to_file = replacement_path

    def get_relative_path(self, path_to_file):
        """ Returns the relaive path from the current bag """
        path = path_to_file
        cur_bag_name = os.path.basename(self.current_bag)
        temp = ""
        relative_path = ""
        while temp != cur_bag_name:
            temp = os.path.basename(path)
            path = os.path.dirname(path)
            relative_path = os.path.join(temp, relative_path)
        return relative_path

    def write_rename_file(self, path_to_dir, file_renamed):
        """ Makes a rename file in CURRENT_BAG\data\meta, returns a path to the file"""
        #Create the path the the rename file
        #make sure the rename file is stored in the correct location
        path_to_meta = self.check_file_structure(self.current_bag)
        rename_file_path = os.path.join(path_to_meta, "renames")
        #create an outfile
        out_file = ""
        append_to_old_file = True
        #If the rename file already exist in this directory, append to it
        if os.path.exists(rename_file_path + ".csv"):
            out_file = open(rename_file_path + ".csv", "ab")
        #If it des not exist, open a new file
        else:
            #print "making rename file...." 
            out_file = open(rename_file_path + ".csv", "wb")
            append_to_old_file = False
        #Set up a CSV writer that will write in UTF-8 format
        unicode_writer = UnicodeWriter(out_file, dialect=csv.excel, encoding="utf-8", delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
        #If not using an already created file, write the headers
        #If it is a new file, create the headers
        if not append_to_old_file:
            unicode_writer.writerow(["Old_Name", "New_Name", "Date"])
        for i in file_renamed:
            #make sure everything is in UTF-8 format
            i.encode("utf-8")
        #If the the list does not already have the date appended, append the date
        if len(file_renamed) == 2:
            file_renamed.append(str(self.now))
        #write the row
        unicode_writer.writerow(file_renamed)
        out_file.close()

    def write_error_file(self, path_to_file):
        """ writes to an error file in the top directory"""
        #Create the path the the rename file
        error_file_path = os.path.join(self.top_directory,"errors_" + self.datestamp)
        #create an outfile
        out_file = ""
        append_to_old_file = True
        #If the rename file already exist in this directory, append to it
        if os.path.exists(error_file_path + ".csv"):
            out_file = open(error_file_path + ".csv", "ab")
        else:
            out_file = open(error_file_path + ".csv", "wb")
            append_to_old_file = False
        unicode_writer = UnicodeWriter(out_file, dialect=csv.excel, encoding="utf-8", delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
        #If not using an already created file, write the headers
        if not append_to_old_file:
            unicode_writer.writerow(["Path of failed file", "Date"])
        path_to_file.encode("utf-8")
        #write the data, using UTF-8
        unicode_writer.writerow([path_to_file, str(self.now)])
        out_file.close()

#https://docs.python.org/2/library/csv.html
#Using a csv writer from this link
#writes csv files in UTF-8
#This was we can represent weird characters that might show up
class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """
    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch utf-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

#usage_message and main largely from data_accessioner.py
def usage_message():
    """ returns a usage message """
    print "\nname_cleanser: Cleanses the file names in a directory.\n \
    This program stores any renamed files in each bag in BAGNAME\\data\\meta\\renames.csv\n \
    If it fails to rename a file due to permission errors, \n it will store those errors in the file errors_YEAR_MONTH_DAY.csv in the top directory\
    \n\nUsage:\
            \n\tpython name_cleanser.py [options] <path>\
            \n\tpython name_cleanser.py -h | --help\
        \n\nOptions:\
            \n\t-h --help\tShow this screen.\
            \n\t-d --debug\tCopies orignal directory into <path>-copy.\
        \n\nDependencies:\
            \n\tcleanse_settings.txt"

def main():
    #If the incorrect number of arguments or the help command
    if len(sys.argv) <= 1 or len(sys.argv) > 3 or sys.argv[1] == "-h" or sys.argv[1] == "--help":
        return usage_message()
    elif len(sys.argv) == 2:
        path_arg = sys.argv[1]
    elif len(sys.argv) == 3:
        path_arg = sys.argv[2]
    #checks to make sure the path exists
    if os.path.exists(path_arg):
        #sets up a NameCleanser object
        cleanser = NameCleanser("cleanse_settings.txt", path_arg)
        #if debug, copy the directory
        if sys.argv[1] == "-d" or sys.argv[1] == "--debug":
            print "Copying files for debugging...."
            if os.path.exists(path_arg + "_copy"):
                shutil.rmtree(path_arg)
                shutil.copytree(path_arg + "_copy", path_arg)
            else:
                if os.path.isdir(path_arg):
                    shutil.copytree(path_arg, path_arg + "_copy")
        print "Cleansing file names... \n------------"
        #start the cleansing process
        cleanser.iterate_through_dir(path_arg, -1)
        print "Done"
        print "Files cleansed:", cleanser.filenumber
        if cleanser.errornum > 0:
            print "There were", cleanser.errornum, "errors. Please check the error file in", path_arg

    else:
        print "\n<path> does not exist",
        usage_message()

main()       
