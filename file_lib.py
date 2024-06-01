import os
import glob

from param_repo import *

DBG = 0

sign_strt_link = "<!-- start_links -->"

def README_add_links ():
     
    file_link = open(f"links.md", "r", encoding="utf-8") 
    file_RDME = open(f"README.md", "a+", encoding="utf-8") 
    
    pos_sign = 0
    file_RDME.seek(0)
    #clean links
    for line in file_RDME.readlines():

        pos_sign += len(line)+1 #\n == CRLF
        if sign_strt_link in  line :
           file_RDME.truncate(pos_sign)
           file_RDME.flush()
           print(f"pos_sign={pos_sign}") 

           break

           
    #insert lines
    str_links = file_link.readlines()

    file_RDME.writelines(str_links)

    file_link.close()    
    file_RDME.close()    


def get_file_name(path):
	if not os.path.isdir(path):
		return os.path.splitext(os.path.basename(path))[0].split(".")[0]


def get_dir_name ( full_file_name):
    # dirname = os.path.basename(full_path_file_name)
    dirname = os.path.dirname(full_file_name)
    return dirname

def file_ranames_to_rate_lngs (lng_rate, path ) :

    ext = 'md'
    file_link = open(f"links.md", "w", encoding="utf-8") 
    list_files = glob.glob( f'{path}/*.{ext}')

    for full_path_to_file in list_files:
        
        # print( f'full_path_to_file ={full_path_to_file}')

        file_name = get_file_name(full_path_to_file)
        
        if DBG == 1:
            print ( f'file_name={file_name}+ {file_name[3:]}')

        for ind,el in enumerate(lng_rate) :
            
            cnt_stars   = el[1]
            lng_name    = el[0]
            if DBG == 1:
                print( f'lng={cnt_stars} lng_name={lng_name}')

            if lng_name in file_name and (len(lng_name) == len(file_name[3:]) ) :
                
                dir_name = get_dir_name( full_path_to_file)
                new_name = f'{path}/' + "%02d" % (ind+1) + '_' + str(lng_name) + "." + ext

                try:
           
                    # os.rename(full_path_to_file, new_name)
                    if DBG == 1 :
                        print (f'full_path_to_file={full_path_to_file} , new_name={new_name}')
                    # break 
                except IOError:
                    continue  

                # Gen links
                _str = f'* [{lng_name}](https://github.com/{repo_user_name}/{repo_name}/blob/master/{new_name}) \n'
                file_link.write (_str)

                print (_str)

        


                 

     