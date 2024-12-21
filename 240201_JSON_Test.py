#!/usr/bin/env python
# coding: utf-8

import uml_V2.uml_lib.ebAPI_lib as ebAPI

def main():

    project_data = ebAPI.getDataFromCache("ActiveProjects")
    print('Active Projects data imported')
    for p in range(0,10): # see if you can work with chatGPT to get how many active projects
        print(project_data[p]["name"]) # change "name" to another field name, like "Project Planner"
        #print(project_data[p]["Project Planner"]) # change "name" to another field name, like "Project Planner"
        currPlanner = project_data[p]["Project Planner"]
        if currPlanner == None:
            print("No planner assigned!")



if __name__ == "__main__":
    main()



