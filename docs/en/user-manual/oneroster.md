---
layout: default  
lang: en  
nav_link: Command Parameters  
nav_level: 2  

nav_order: 80  
---  


# Oneroster and Student Information Systems  (SIS)

---

[Previous Section](deployment_best_practices.md)  

---

## What is Oneroster?
Oneroster is not actually an application, but a specification.  Oneroster simplifies the management of rostering for education by standardizing the format for REST and CSV data handling.  This makes it easier for service applications (such as Adobe) to integrate with SIS (student information systems) platforms  that comply with the standard.  It is in a school's best interest to choose Oneroster standardized platforms, because it greatly simplifies the process of maintaining a synchronous state between their rostering breakdown and the products their users need access to.  An in-depth description of the standard can be found on the Oneroster homepage (IMS Globlal):

[https://www.imsglobal.org/activity/onerosterlis](https://www.imsglobal.org/activity/onerosterlis "https://www.imsglobal.org/activity/onerosterlis")

According to IMS, the big picture features of the standard include the following:

- Provision key roster related data including student, course and related enrollment information between various platforms such as a student information system (SIS) and a learning management system (LMS).
- Flexible implementation options to align with an institution’s needs and capabilities, supporting simple spreadsheet-style (CSV) exchanges as well as system-to-system exchanges using REST API’s
- Improves data exchange among multiple systems with roster and gradebook information, thus eliminating problems before they happen
- Transmit scored results between applications, such as student scores from the LMS back to the SIS.

The Oneroster API is open source by definition, which means that all information regarding endpoints and data models is freely available in the actual specification.  The specification provides detailed guidance as to API structure.  Since all the major SIS players adopt the standard and provide similar access to it, the Oneroster connector enables flexibility to do rostering based provisioning - a highly desirable feature!  Adobe works with a great deal of educational organizations.  Most, if not all of these organizations already leverage SIS that include the Oneroster API/CSV implementation.  Some examples of these SIS are:

- Classlink
- Clever
- Kivuto
- Infinite Campus
- Powerschool

## SIS and User Sync

Before the creation of this connector, the only option for EDU was to use the sync tool via active directory for synchronization (the standard approach outlined in the [setup and success guide](../success-guide/index.md).  This allowed some limited ability to assign permanent licenses to faculty/staff, but there wass no way to provision licenses based on actual rostering data - e.g., students in Art 101 should have access to CCE products, but ONLY for one semester.  Another alternative was to use the Oneroster compliant CSV exports to modify the admin console directly - a tedious and difficult to manage process.

The Oneroster connector for UST now offers a better approach, by utilizing a direct interface with the SIS platforms, which means that the sync tool is able to leverage the full rostering information the institution is used to using with other services.  The decisions as to which  way to group users (i.e., based on class, course, school, etc) are flexible enough to allow a wide range of potential configurations in an easy to use fashion.


## Installation
1. First, download the MSI installer for UST (if you are on windows).  If you are not using windows, you can run the python install script to get the sync tool in place.  Both of these can be found on the [UST Installation page](https://github.com/adobe/UST-Install-Scripts "UST Installation page").  Once you've done this, you should have a folder as shown below.  Please ignore the **"Configure UST"** application - this wizard is for LDAP configuration, and will work with the Oneroster connector!

     ![](https://github.com/adobe-dmeservices/user-sync.py/blob/oneroster_documentation/docs/en/user-manual/media/ust_directory.png?raw=true)

2. Go into the examples\basic folder, and copy the file named **connector-oneroster.yml** to the root directory.  You can also go ahead and delete **connector-ldap.yml** as you will not need it.  This will help to avoid confusion by future users.  To edit the YAML files, just run **"Edit YAML"** - this will open them with the embedded Notepad++ editor.  You should now be able to edit **connector-umapi.yml**, **connector-oneroster.yml**, and **user-sync-config.yml**.

2. Follow the directions for the UMAPI integration below using the certificate created during the installation process. (This file will be in your install directory, named **certificate_pub.crt**).  If the certificate is missing or you need to recreate it, just run the **Adobe.IO Certgen** application.  On linux, you can run **ssl_certgen.sh**.

3. Once you have the credentials created on the UMAPI page, go ahead and enter them into the server section of **connector-umapi.yml**.  NOTE - you do not need the field from the UMAPI entitled **"technical account email"**.  The tech_acct field shown below should be populated with the **"technical account ID"** instead!

    ```yaml
    enterprise:
        org_id: "Org ID goes here"
        api_key: "API key goes here"
        client_secret: "Client secret goes here"
        tech_acct: "Tech account ID goes here (NOT tech account email!)"
        priv_key_path: "private.key"
    ```
5. Edit the file called **user-sync-config.yml**.  Comment out the field `ldap: "connector-ldap.yml"` near line 132 by adding a '#' symbol before it.  Next, uncomment the field: `    oneroster: "connector-oneroster.yml"`. You can also open up both of the .bat files (Run test and Run live), and append: "--connector oneroster". E.g:

    `python user-sync.pex --process-groups --users mapped --connector oneroster`

    Once these steps are complete, UST is configured to use the Oneroster connector as its identity source, and you can proceed to the configuration section.


## Configuration

1. Edit the file named **connector-oneroster.yml**.  The required settings are shown below. You can find some default values for these fields in the connector. (NOTE: there are additional optional settings available.  Please read the comments in the connector to learn more about them).  

    ```yaml
    connection:
        platform: 'clever or classlink'	#Only clever and classlink are supported for now
        client_id: 'api client id here'	#From your SIS dashboard
        client_secret: 'api client secret here'	#From your SIS dashboard
        host: 'https://api.clever.com/v2.1/ for clever or your oneroster URL for classlink'
    
        #access_token: 'api token (clever only)'  #Optional - if added, the client id and secret fields are not needed. Uncomment to use'
        page_size: 3000		#API page size - limited by what the platform allows.  Leave as high as possible for faster sync.
        max_user_count: 0	#limits the number of users returned by the API (useful for testing)
    
    schema:
        match_groups_by: 'name'		# which oneroster field to use for matching group names to sections, classes, courses or schools
        key_identifier: 'id'	# Field by which objects are identified in Oneroster - typically sourcedId or id
        all_users_filter: 'users'	# When using --users all, this option determines what user types are fetched (can be students, teachers, or users)
        default_group_filter: 'sections'	# Default choice for group filter if none specified
        default_user_filter: 'students'		# Default choice for user filter if none specified
    ```
2. Fill out the connection settings.  You MUST enter either 'clever' or 'classlink' for the platform type, though additional platforms may be supported in the future.  The client ID and secret should come from your SIS dashboard (see the prerequisites section above).  These keys enable UST to connect to your Oneroster instance.  The hostname can be set as noted above for clever, or as your classlink URL for classlink.  This may look like:  `https://example-ca-v2.oneroster.com/ims/oneroster/v1p1/` or similar.

	The page size and max user count can be ignored and set to default (see the comment above if you want to use them).  Likewise, the access token field can also be ignored.  This  field is only valid for clever - and, if set, will override the client id and secret paramters.  This provides and alternative configuration that doesn't require the API credentials.

3. In the schema section, you can configure the default settings for your API.  Please read the comments above for a description of these fields.  The two which should be considered carefully are the match groups and key identifier settings.  If these are not set according to your platform (classlink vs clever) and group name conventions, you will not be able to sync users.

4. For information on available configuration options, please see the documentation (NOT ADDED YET).  Instead, we provide some examples of what this file might look like for the cases of clever and classlink:

	For **Clever**: 
    ```yaml
    connection:
        platform: 'clever'
        client_id: 'api client id here'
        client_secret: 'api client secret here'
        host: 'https://api.clever.com/v2.1/'
    
        access_token: 'TEST_TOKEN'
        page_size: 3000
        max_user_count: 0
    
    schema:
        match_groups_by: 'name'
        key_identifier: 'id'
        all_users_filter: 'users'
        default_group_filter: 'sections'
        default_user_filter: 'students'
    ```
	For **Classlinkr**: 
    ```yaml
    connection:
        platform: 'classlink'
        client_id: 'api client id here'
        client_secret: 'api client secret here'
        host: 'https://example-ca-v2.oneroster.com/ims/oneroster/v1p1/'
    
        page_size: 3000
        max_user_count: 0
    
    schema:
        match_groups_by: 'title'
        key_identifier: 'sourcedId'
        all_users_filter: 'users'
        default_group_filter: 'classes'
        default_user_filter: 'students'
    ```


## UMAPI Integration
1.  Sign into the [Adobe I/O Console](https://console.adobe.io "Adobe I/O Console"), select your organization from the drop-down list, and click New Integration. <br/><br/>
![](https://github.com/adobe-dmeservices/user-sync.py/blob/oneroster_documentation/docs/en/user-manual/media/umapi/step_1.gif?raw=true)
<br/><br/>2. In the Create a New Integration wizard, select Access an API, and click Continue.<br/><br/>
![](https://github.com/adobe-dmeservices/user-sync.py/blob/oneroster_documentation/docs/en/user-manual/media/umapi/step_2.png?raw=true)
<br/><br/>3. Select User Management API under Adobe Services, and click Continue. On the screen that appears next, click Continue again.<br/><br/>
![](https://github.com/adobe-dmeservices/user-sync.py/blob/oneroster_documentation/docs/en/user-manual/media/umapi/step_3.gif?raw=true)
<br/><br/>4. Enter a name and description for the integration, and upload the Public key certificate file. Click Create integration.<br/><br/>
![](https://github.com/adobe-dmeservices/user-sync.py/blob/oneroster_documentation/docs/en/user-manual/media/umapi/step_4.png?raw=true)
<br/><br/>5. To view the integration details, click Continue to Integration Details.<br/><br/>
![](https://github.com/adobe-dmeservices/user-sync.py/blob/oneroster_documentation/docs/en/user-manual/media/umapi/step_5.png?raw=true)

<br/>
<br/>
<br/>
<br/>

<br/>&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;
<br/>TO BE WRITTEN (Below)
<br/>&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;

## Prerequisites
Prereqs should include creating and registering the UST application on the SIS console.  This depends on the platform - i.e., Clever vs Classlink.  Once this is done, API credentials should be secured for use with UST connector.

## Configuration
The big one on configuring the connector and user-sync-config
## Testing and first sync
Not sure - probably utilize max user limit to sync just a few test users
## Running the full sync
TBD for this one

<br/>&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;
<br/>TO BE USED (Below)
<br/>&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;

```yaml
- directory_group: "Faculty"
    adobe_groups:
        - "All apps"
```

The Oneroster specific format looks more like the following:

```yaml
- directory_group: "classes::ELA 6 (6A ELA)::teachers"
    adobe_groups:
        - "All apps"
```

This indicates that we want to map all teachers for the class named ELA 6 to the "All apps" group.  At first this appears unecessary - but consider the following scenario:

```yaml
- directory_group: "classes::ELA 6 (6A ELA)::students"
    adobe_groups:
        - "All apps"
- directory_group: "courses::ART 101::teachers"
    adobe_groups:
        - "All apps"
- directory_group: "schools::Spring Valley::users"
    adobe_groups:
        - "Spark"
```

Now, we are able to say: all ART 101 teachers get cce for the school year, but students only get access if they are ELA 6 and only for that semester.  If instead, we were to follow the default convention of name only, these mappings could not coexist in the same sync tool.  The reasons for allowing this flexibility become clear considering that wile we technically could get away with only allowing classes, it may become quickly complex when we consider that schools typically might need to map hundreds of classes at any given time.  This approach allows for granular mapping as well as high level mapping for maximum configurability.  In a general sense, this strategy looks like the following; 

```yaml
- directory_group: "{group filter}::{group name}::{user filter}"
```
where,

group filter: the kind of object to which group name is evaluated against.  The options are schools, courses, and classes
group name: the actual name of the class, course, or school which we want to find users in.  This is currently the "title" field from the above tables for classes/courses, and the "name" attribute for schools
user filter: which kind of users are we trying to map? The options are students, teachers, or users (both) 
The bottom line of this mapping strategy yields a situtation where the ust can be quickly and easily configured to target groups (courses, classes, or schools) and users (teachers, students, users), mixing and matching as necessary to meet their goals.  The default values can be set in the connector-oneroster.yml file.  The default values are likey to be classes/users or classes/students.  With defaults, one must only enter the "group" name as usual.  Therefore, 

```yaml
- directory_group: "classes::ELA 6 (6A ELA)::students"
    adobe_groups:
        - "All apps"
```

Could be reduced to:

```yaml
- directory_group: "ELA 6 (6A ELA)"
    adobe_groups:
        - "All apps"
```
&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>

[Previous Section](deployment_best_practices.md)
