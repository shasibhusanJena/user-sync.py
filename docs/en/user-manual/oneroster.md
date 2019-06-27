---
layout: default  
lang: en  
nav_link: Command Parameters  
nav_level: 2  

nav_order: 80  
---  


# Oneroster and Student Information Systems  

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

[![](https://www.imsglobal.org/sites/default/files/developers/integrateddigitalcurriuclumflow.png)](https://www.imsglobal.org/sites/default/files/developers/integrateddigitalcurriuclumflow.png)

The Oneroster API is open source by definition, which means that all information regarding endpoints and data models is freely available in the actual specification.  The specification provides detailed guidance as to API structure.  Since all the major SIS players adopt the standard and provide similar access to it, the Oneroster connector enables flexibility to do rostering based provisioning - a highly desirable feature!  Adobe works with a great deal of educational organizations.  Most, if not all of these organizations already leverage SIS that include the Oneroster API/CSV implementation.  Some examples of these SIS are:

- Classlink
- Clever
- Kivuto
- Infinite Campus
- Powerschool

## SIS and User Sync

Before the creation of this connector, the only option for EDU was to use the sync tool via active directory for synchronization (the standard approach outlined in the [setup and success guide](../success-guide/index.md).  This allowed some limited ability to assign permanent licenses to faculty/staff, but there wass no way to provision licenses based on actual rostering data - e.g., students in Art 101 should have access to CCE products, but ONLY for one semester.  Another alternative was to use the Oneroster compliant CSV exports to modify the admin console directly - a tedious and difficult to manage process.

The Oneroster connector for UST now offers a better approach, by utilizing a direct interface with the SIS platforms, which means that the sync tool is able to leverage the full rostering information the institution is used to using with other services.  The decisions as to which  way to group users (i.e., based on class, course, school, etc) are flexible enough to allow a wide range of potential configurations in an easy to use fashion.

## Prerequisites
## Installation
## Configuration
## Testing and first sync
## Running the full sync



TO BE MODIFIED LATER:

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

<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>

[Previous Section](deployment_best_practices.md)
