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

Before the creation of this connector, the only option for EDU was to use the sync tool via active directory for synchronization (the standard approach outlined in the [setup and success guide](../success-guide/index.md)).  This allowed some limited ability to assign permanent licenses to faculty/staff, but there wass no way to provision licenses based on actual rostering data - e.g., students in Art 101 should have access to CCE products, but ONLY for one semester.  Another alternative was to use the Oneroster compliant CSV exports to modify the admin console directly - a tedious and difficult to manage process.

The Oneroster connector for UST now offers a better approach, by utilizing a direct interface with the SIS platforms, which means that the sync tool is able to leverage the full rostering information the institution is used to using with other services.  The decisions as to which  way to group users (i.e., based on class, course, school, etc) are flexible enough to allow a wide range of potential configurations in an easy to use fashion.


## Installation
1. First, download the MSI installer for UST (if you are on windows).  If you are not using windows, you can run the python install script to get the sync tool in place.  Both of these can be found on the [UST Installation page](https://github.com/adobe/UST-Install-Scripts "UST Installation page").  Once you've done this, you should have a folder as shown below.  Please ignore the **"Configure UST"** application - this wizard is for LDAP configuration, and will work with the Oneroster connector!

     ![](https://github.com/adobe-dmeservices/user-sync.py/blob/oneroster/docs/en/user-manual/media/ust_directory.png?raw=true)

2. Go into the examples\basic folder, and copy the file named **connector-oneroster.yml** to the root directory.  You can also go ahead and delete **connector-ldap.yml** as you will not need it.  This will help to avoid confusion by future users.  To edit the YAML files, just run **"Edit YAML"** - this will open them with the embedded Notepad++ editor.  You should now be able to edit **connector-umapi.yml**, **connector-oneroster.yml**, and **user-sync-config.yml**.

2. Follow the directions for the [UMAPI integration guide](https://adobeio-prod.adobemsbasic.com/authentication/auth-methods.html#!AdobeDocs/adobeio-auth/master/AuthenticationOverview/ServiceAccountIntegration.md "UMAPI integration guide") using the certificate created during the installation process. (This file will be in your install directory, named **certificate_pub.crt**).  If the certificate is missing or you need to recreate it, just run the **Adobe.IO Certgen** application.  On linux, you can run **ssl_certgen.sh**.  **NOTE:** You only need to follow steps 1 and 3.  In step 1, choose the "User Management API" for the type.

3. Once you have the credentials created on the UMAPI page, go ahead and enter them into the server section of **connector-umapi.yml**.  NOTE - you do not need the field from the UMAPI entitled **"technical account email"**.  The tech_acct field shown below should be populated with the **"technical account ID"** instead!

    ```yaml
    enterprise:
        org_id: "Org ID goes here"
        api_key: "API key goes here"
        client_secret: "Client secret goes here"
        tech_acct: "Tech account ID goes here (NOT tech account email!)"
        priv_key_path: "private.key"
    ```
5. Edit the file called **user-sync-config.yml**.  Comment out the field `ldap: "connector-ldap.yml"` near line 132 by adding a '#' symbol before it.  Next, uncomment the field: `    oneroster: "connector-oneroster.yml"`. Also, change connector near the bottom in the invocation defaults section from "ldap" to "oneroster".  Once these steps are complete, UST is configured to use the Oneroster connector as its identity source, and you can proceed to the configuration section.  When you're finished, your configuration file should include the following (some areas have been omitted as they are defaults).

    ```yaml
    directory_users:
          user_identity_type: federatedID
          default_country_code: US
          connectors:
              # ldap: "connector-ldap.yml"
              oneroster: "connector-oneroster.yml"
          groups: "[Omitted for clarity]"

    invocation_defaults:
          adobe_only_user_action: preserve
          adobe_only_user_list:
          connector: oneroster
          process_groups: Yes
          strategy: sync
          test_mode: No
          update_user_info: No
          user_filter:
          users: mapped
    ```


## Connector Configuration

    
1. Edit the file named **connector-oneroster.yml**.  The required settings are shown above. You can find some default values for these fields in the connector itself. (NOTE: there are additional optional settings available.  For a full list and description, please see the table at the end of this page).  

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

3. In the schema section, you can configure the default settings for your API.  The two which should be considered carefully are the match groups and key identifier settings.  If these are not set according to your platform (classlink vs clever) and group name conventions, you will not be able to sync users. The other options are filters that determine what kind of data can be fetched.  The default group and user filters will be explained in the next section as they apply directly to the group mapping configuration.  

	Lastly, the all_users_filter (as indicated in the comments above) is only applicable when the --users all command is specified on the command line or in place of --users mapped in the user-sync-config.yml.  This filter determines exactly which user types are pulled in by --users all.  You can set it to students, teachers, or users (both).  This setting does not affect the group filters.  

	To help make the configuration clearer, please look at the examples below.  These show how one can configure the connector for both cases of clever and classlink.  In the clever example, an access token (TEST_TOKEN) is shown.  Using this token will allow to access the Clever sandbox data for testing purposes.  You should replace this or comment it out,  using the client_id and client_secret to access your real API.

	For **Clever:** 

    ```yaml
    connection:
        platform: 'clever'
        access_token: 'TEST_TOKEN'
        host: 'https://api.clever.com/v2.1/'    
        
        page_size: 3000
        max_user_count: 0
    
    schema:
        match_groups_by: 'name'
        key_identifier: 'id'
        all_users_filter: 'users'
        default_group_filter: 'sections'
        default_user_filter: 'students'
    ```
    
    For **Classlink:**

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

## Groups Configuration

The final step to configuring the connector will be to specify the group mappings.  Under normal LDAP circumstances, we refer to a "group" as an AD security group.  In order to tell UST what groups to query, we simply enter the common name of the group into user-sync-config.yml in the groups section, and indicate which Adobe side group it should be mapped to.  

For Oneroster, the concept of a group is somewhat different, since it is in no way a "directory" of users.  Instead, one is forced to make an arbitrary decision about what constitutes a "group".  At the base level, a "group" is meant to specify which users are to by synced.  Expanding this definition to the Oneroster schema, which includes categories like schools, classes/sections, courses, we can see that some likely categories that we might want to use to group our users by.  The cache?  There are now multiple group definitions to manage!  The connector is designed around this concept of variable group type (unlike the other connector types, which allow only one definition of a group).

The actual implementation and configuration options are best demonstrated by example.  In this step, we will modify the **groups** key in **user-sync-config.yml** (near line 174).  Consider the following default value, which is a normal LDAP type group mapping.  In this example, we are instructing UST that the group named "Acrobat_DC_Pro_Users" should be assigned to a like-named group on the Admin Console.  Here, the definition of a group (security group) and its name (the common name) are quite clear, and no further instruction is warranted.

```yaml
 - directory_group: "Acrobat_DC_Pro_Users"
          adobe_groups:
                  - "Acrobat DC Pro Users"
```

To translate this to a variable group type context, we add some extra information that serves to specify the kind of group we want to get, along with what user type.  In this model, the user types are also multivalued and are allowed to change from group to group.  Consider the following modification of the above code:

```yaml
 - directory_group: "courses::Econ 101::students"
          adobe_groups:
                  - "Acrobat DC Pro Users"
```
We have appended "courses" and "students" on the name of a course.  By doing so, we tell UST that we want the **course** named "Econ 101" (as opposed to a class by that name or some other conflict), and that we wish to map only the students from the class, instead of users (students + teachers) or just teachers.  It should become immediately clear that by adding the qualifiers, we are now free to us more complex mappings that allow for any combination of group types and user types.  For example, the following chunk:

```yaml
- directory_group: "sections::Class 003, Homeroom - Stark - 0::users"
        adobe_groups:
              - "Spark"
- directory_group: "courses::Class 001, Homeroom::students"
        adobe_groups:
              - "Spark"
              - "All Apps"
- directory_group: "schools::Rockaway Beach Middle School::teachers"
        adobe_groups:
              - "Pro DC"
```

In the above example, we choose to map users for "Class 003, Homeroom - Stark - 0" to the spark group.  Next, we take the students from Homeroom Class 001 (a course, rather than a class), and assign them spark and all apps.  In the last example, we map all teachers at Rockaway Beach Middle School to a pro dc group.  It should be apparent now that we can construct any combination of group types (referred to as "group_filter" in the connector), user types (user_filter) and group names that we desire.  Generalizing this idea,

```yaml
- directory_group: "{group filter}::{group name}::{user filter}"
```
where the following values are allowed:<br/>

| Field |Allowed value   |
| ------------ | ------------ |
|  {group filter} | schools, courses, classes or sections   |
| {user filter}  | students, teachers or users  |
| {group name}| the value to match on (in this case a literal name)|

We can take this one step further, to simplify our group mappings again in some cases.  Consider the case where we want to map many sections, and they will all be using students.  Rather than type out the above string for every case, we  can tell UST what these ought to be by *default*.  That is to say, it will automatically append the filters - and therefore we don't have to!  This is meaning of the fields "default_user_filter" and "default_group_filter" in the configuration settings in the previous section.  If we indicate our default group filter as sections, and the default user filter as students, we can simply write:  

```yaml
- directory_group: "Class 003, Homeroom - Stark - 0"
        ....
- directory_group: "Class 001, Homeroom - Ericcson - 0"
        ....
- directory_group: "Section #3"
        ....
```
By doing so, we have reduced the mappings back to being simple.  Furthermore, we can continue to mix and match if we like, eg:

```yaml
- directory_group: "Class 003, Homeroom - Stark - 0"
        ....
- directory_group: "Class 001, Homeroom - Ericcson - 0"
        ....
- directory_group: "schools::Rockaway Beach Middle School::teachers"
        ....
```
In this way we provide maximum flexibility with the options for standard simple group mappings.

### The group matching definition
In the above discussion, we did leave out a key piece of information - we have implicitly assumed that all of our target objects have a "name" filed that we can match (like "Class 003...").  But, what if we need to match on a unique identifier instead (like SIS_ID, id, sourced id) or on some other custom field (course number, etc).  Why should we be forced to use the name?  Answer: we are not!  The field named "match_groups_on" in connector-oneroster.yml allows you to specify exactly what you want to match with your group name.  This can be set to any available field on the target object (according to the api schema).  In the default configuration, it is set to "name" for clever and "title" for classlink.  This could just as easily be "sourcedId" or some other field.  Assuming for the moment that we have set "match_groups_on" to **sourcedId**, we could write our groups query as follows (assuming that "5cfb063268d44802ad7b2fb8" is the sourcedId for the section of interest):

```yaml
- directory_group: "sections::5cfb063268d44802ad7b2fb8::students"
```

Or simply, if we are using the simplified notation:
```yaml
- directory_group: "5cfb063268d44802ad7b2fb8"
```

At this time, it is only possible to specify a global match parameter -- e.g., using sourcedId means ALL group mappings must match by this - you can't use sourcedId for one and name for another.  This flexibility may be added down the line as an additional :: delimited field.


## Testing and first sync

If all has gone well so far, you're ready to do a test sync.  Identify which users you are comfortable pushing to the console.  This could be a small class, or just the teacher of some classes.  Because it is more difficult to manage testing with Oneroster (since you cannot create or manage the groups), we have included a useful feature called max_user_count.   Setting this to a positive, nonzero integer will cause the API calls to cutoff early, and the number of returned users will never exceed this setting.  

Add the class/course/section/school into **user-sync-config.yml** as per the notation above, using either the fully qualified "::" syntax, or in the simplified format using the default filters.  If you intend to sync "all", then make sure you have set --users **all** in the batch files (mapped is default).  When you are ready, execute **Run_UST_test_mode.bat**.  This will run UST using the standard default parameters.  Barring any errors, you should see something similar to the below.  In this example, 4 students and 1 teacher were found and processed (but not pushed to the console, as it was run in test mode).  If all looks good, you are ready to configure the rest of your groups and start syncing! 

```plain
INFO config - Using main config file: ..\oneroster-config\oneroster-user-sync-config.yml (encoding utf8)
INFO main - ========== Start Run (User Sync version: 2.5.0rc2) =========
INFO main - Python version: 3.6.8 on win32
INFO main - ------- Command line arguments -------
INFO main - -c ..\oneroster-config\oneroster-user-sync-config.yml -t --process-groups --users mapped
INFO main - -------------------------------------
INFO processor - ---------- Start Load from Directory -----------------------
INFO clever - Getting users from: https://api.clever.com/v2.1/sections/58da8c6b894273be680001fc/students
INFO clever - Collected users: 4
INFO clever - Getting users from: https://api.clever.com/v2.1/sections/58da8c6b894273be680001fc/teachers
INFO clever - Collected users: 1
INFO oneroster - Found 21 total users
INFO processor - ---------- End Load from Directory (Total time: 0:00:05) ---
INFO processor - ---------- Start Sync with UMAPI ---------------------------
INFO processor - Creating user with user key: federatedID,harvey.karen@resistanceisfutile.net,
INFO processor - Creating user with user key: federatedID,sawayn.adrianna@resistanceisfutile.net,
INFO processor - Creating user with user key: federatedID,dietrich.jonathan@resistanceisfutile.net,
INFO processor - Creating user with user key: federatedID,o'connell.george@resistanceisfutile.net,
INFO processor - Creating user with user key: federatedID,herman.kevin@resistanceisfutile.net,
INFO processor - ---------- End Sync with UMAPI (Total time: 0:00:09) -------
INFO processor - ---------------------------- Action Summary (TEST MODE) ----------------------------
INFO processor -                         Number of directory users read: 5
INFO processor -           Number of directory users selected for input: 5
INFO processor -                             Number of Adobe users read: 22
INFO processor -            Number of Adobe users excluded from updates: 2
INFO processor -     Number of non-excluded Adobe users with no changes: 0
INFO processor -                        Number of new Adobe users added: 5
INFO processor -                 Number of matching Adobe users updated: 0
INFO processor -                    Number of Adobe user-groups created: 0
INFO processor -       Number of Adobe-only users with groups processed: 20
INFO processor -   Number of UMAPI actions sent (total, success, error): (5, 5, 0)
INFO processor - ------------------------------------------------------------------------------------
INFO main - ========== End Run (User Sync version: 2.5.0rc2) (Total time: 0:00:16) 
```

# Reference

## Errors and definitions
Compiled errors from testing..?

## Table of parameters and descriptions

|Field                    |Type                                    |Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |Example                                                                                          |
|-------------------------|----------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
|**Connection**|++++++++++++|+++++++++++++++++++++++++++++++++++++++++++++++++++++||
|platform                 |required (no default)                   |specifies which platform to use.  Can ONLY be one of: [classlink, clever]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |clever                                                                                           |
|client_id                |required if no access_token (no default)|Client ID from SIS dashboard                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |5d8a7b5eff61ga25bc6e                                                                             |
|client_secret            |required if no access_token (no default)|Client Secret from SIS dashboard                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |c6d2c6745c12ae785f7f1a58a307a04cf0a4                                                             |
|host                     |required (no default)                   |Endpoint for organization's OneRoster implementation                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |Clever: https://api.clever.com/v2.1/ Classlink: https://example.oneroster.com/ims/oneroster/v1p1/|
|access_token             |optional (no default)                   |Allows to bypass API authentication for Clever.  Mainly useful for testing (use 'TEST_TOKEN') or to avoid putting credentials into the file.                                                                                                                                                                                                                                                                                                                                                                                                                           |TEST_TOKEN                                                                                       |
|page_size                |optional (default: 1000)                | api call page size.  Adjusting this will adjust the frequency of API calls made to the server                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |3000                                                                                             |
|max_user_count           |optional (default: 0)                   |API calls will cutoff after this many users.  Set to 0 for unlimited.  Useful when doing test runs to avoid pulling very large user counts.                                                                                                                                                                                                                                                                                                                                                                                                                            |0, 10, 50, 4000, etc…                                                                            |
|**Schema**                   |                                        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |                                                                                                 |
|match_groups_by          |required (default: name)                |Attribute corresponding to the group name in user-sync-config.yml.  UST will match the desired value to this field (e.g., name, sourcedId, etc…).  For clever, "name" will suffice for schools, courses and sections.  For classlink, you can user "title" for classes/courses, and "name" for schools.                                                                                                                                                                                                                                                                                                                                                                                                                       |title, name, SIS_ID, sourceId, subject                                                           |
|key_identifier           |required (default: sourcedId)           | unique key used throughout One-Roster (sourcedId or id commonly used).  This may not be an arbitrary value, since it is used in the URL of the API calls.  It must exist and be the base ID for your platform.                                                                                                                                                                                                                                                                                                                                                        |sourcedId, id                                                                                    |
|all_users_filter         |required (default: users)               |all users filter.  Use this with the --users all command line option to target all users.  Available choices are [students, teachers, users]                                                                                                                                                                                                                                                                                                                                                                                                                           |users, students, teachers                                                                        |
|default_group_filter     |optional (default: classes)             |the default filter applied to the prefix of a plain group name                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |schools, courses, sections, classes                                                              |
|default_user_filter      |optional (default: students)            |the default filter applied to the suffix of a plain group name                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |users, students, teachers                                                                        |
|include_only             |optional (no default)                   | Provide attributes(key) and expected values (value) within the schema section of your implementation.  All users that do not meet the specified criteria will be removed from the sync process                                                                                                                                                                                                                                                                                                                                                                        | gender: "F"  grade: "Kindergarten"                                                              |
|**Other**                    |                                        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |                                                                                                 |
|user_email_format        |optional (default: {email})             |specifies how to construct a user's email address by  combining constant strings with the values of specific Okta profile attributes.  Any names in curly braces are taken as attribute names, and everything including  the braces will be replaced on a per-user basis with the values of the attributes.  The default value is from "email" field in Oneroster.                                                                                                                                                                                                     |{email},{id}@{domain}                                                                            |
|user_domain_format       |optional (no default)                   |used to discover the domain for a given user.  If not specified, the  domain is taken from the domain part of the user's email address.                                                                                                                                                                                                                                                                                                                                                                                                                                |N/A (not typically used for Oneroster)                                                           |
|user_username_format     |optional (no default)                   |specifies how to construct a user's username on the  Adobe side by combining constant strings with attribute values.  Any names in curly braces are taken as attribute names, and everything including  the braces will be replaced on a per-user basis with the values of the attributes.  This setting should only be used when you are using federatedID and your  federation configuration specifies username-based login.  In all other cases,  make sure this is not set or returns an empty value, and the user's username  will be taken from the user's email.|N/A (not typically used for Oneroster)                                                           |
|user_given_name_format   |optional (default: {givenName})         |specifies the field to user for a users first name                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |{sourcedId}, any other attribute                                                                 |
|user_surname_format      |optional (default: {familyName})        |specifies the field to user for a users last name                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |{familyName}, any other attribute                                                                |
|user_country_code_format |optional (no default)                   |specifies the field to user for a users country code.  Normally, Oneroster does not provide this information.                                                                                                                                                                                                                                                                                                                                                                                                                                                          |N/A (not typically used for Oneroster)                                                           |
|user_identity_type_format|optional (no default)                   |specifies the field to user for a users identity type.  Oneroster does not provide this information.                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |N/A (not typically used for Oneroster)                                                           |


[Previous Section](deployment_best_practices.md)
