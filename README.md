#Archives File Name Cleaner
===========================

Code by Caitlin Donahue caitlindonahue95@gmail.com

Derived from Archives Data Accessioner by Liam Everett liam.m.everett@gmail.com and edited by Sahree Kasper sahreek@gmail.com

### General Description:
- Given a database, strips the file names of illegal characters, replacing them with an underscore
- legal characters are alphanumerical characters and underscores
- If a file is renamed it gets stored in BAGNAME\data\meta\renames.csv 
- There will be one renames.csv file for every directory in the directory that is originally passed to the program
- If the program cannot rename a file for some reason it will store the file path in an errors.csv file in the top directory 
- Requires cleanse_settings.txt to be in the same folder as name_cleanser.py

##Installing Python
You will need Python installed on your computer to run this program.
Python can be found here: https://www.python.org/download/releases/2.7.5/
or here: https://www.python.org/download/releases/3.2.2/

Instructions on setting up Pyton on your computer can be found here: https://apps.carleton.edu/curricular/cs/resources/source/python_install/


##Usage Instructions
(Mac) Open a terminal window by navigating to "Applications -> Utilities -> Terminal" and clicking on the Terminal icon
(PC) Open a command prompt by selecting Start/Run and typing cmd and Enter or Start/Programs/Accessories/Command Prompt.

First navigate in your terminal to the folder in which name_cleanser.py is contained.
- cd (path to folder containing name_cleanser.py)

Once in the folder containing name_cleanser.py run it with the following syntax:

    python name_cleanser.py [options] (path to directory to cleanse)
    
or

    python name_cleanser.py (path to directory to cleanse)
    

#### Options:
- These are optional, you can run the program without them
- if you would like to use them, replace [options] with on eof the following
    - -h, --help
        - Will bring up a usage message
    - -d, --debug
        - will copy the directory that name_cleanser is being run on 

#### Input:
 - A full path to a directory OR a directory name in the same folder as data_accessioner.py. 
    -this should be a top directory that holds the directories you want to be cleansed


#### Output:
- DIRECTORYNAME\data\meta\renames.csv for every directory in the top directory
    - this contains the full path of the original file, as well as what it has been renamed to and the timestamp for every file in that directory that as been renamed
    
- errors_YEAR_MONTH_DATE.csv file in the top directory if the program failed to rename any files, containing the path to the failed file and the timestamp here we(if there were any errors)


cleanse_settings.txt Instructions
---------------------------------

In cleanse_settings.txt there are three sections you can modify:

    EXCLUDES:
    ERROR_CHECK_TIME:
    RELATIVE_PATH_TO_RENAMES:

- In EXCLUDES you can put any file or folder names that you would like the name cleanser to check. Note that if you exclude a folder name, the cleanser also will not check anything in that folder. place each entry on a new line.

- In ERROR_CHECK_TIME you control how long to let the system rest if it runs into any errors before retrying them. If you try to enter multiple numbers under this section the program will choose the last.

- In RELATIVE_PATH_TO_RENAMES you control where your renames file will be stored. The renames file will always be stored in the current bag, but you can control the structure of the sub-directories it is stored in. The default for this program is to store the renames files in data/meta under the current bag. If the path defined does not exist the program will create it. Please enter each subdirectory on a seperate line, for example, if we want the path to be data/meta we would have the following:

        RELATIVE_PATH_TO_RENAMES:
        data
        meta
