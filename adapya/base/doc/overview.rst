Overview
========

*adapya-base* provides basic functions used by other adapya packages like
e.g. adapya-adabas. It comes with sample programs and scripts to show its use.


**adapya-base** is a **pure** Python package: it does not require compilation
of extensions, but uses the **ctypes** module.

It has been used on mainframe z/OS, Solaris, z/Linux and Windows.

More adapya packages are available:

- adapya-adabas: Native database API to Adabas
- adapya-era: Client interface to Adabas Event Replication
- adapya-entirex: Client interface to Entirex Broker


Further information on adapya can be found at

http://tech.forums.softwareag.com/techjforum/forums/show/171.page

adapya-base License
-------------------

Copyright 2004-2023 Software AG

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.

You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

See the License for the specific language governing permissions and
limitations under the License.

Change History
--------------
**adapya-base 1.3.0 (December 2023)**

- getfilez binary file transfer without RDW option

**adapya-base 1.2.0 (March 2022)**

- added jesjob script for handling JES queues via FTP (list, reading etc.)


**adapya-base 1.1.0 (January 2021)**

- support of encrypted FTP using TLS with certificates with ftpz and
  getfilez scripts


**adapya-base 1.0.0 (June 2018)**

- jconfig uses keyring package for passwords if installed
- scripts for z/OS file transfer and processing SMF records


**adapya-base 0.9.5 (April 2017)**

- move adapya-base functions into separate defs module
- support of z/OS with the Rocket Python 2.7 and 3.6


**adapya-base 0.9 (September 2016)**

- adapya was split into smaller packages to achieve independence
- support of Python 3.5 and higher
- support of z/OS with the Rocket Python 2.7.12


**Adapya 0.8**

- dtconv.py new routine for date/time conversions

- Datamap added support for

  -  multiple fields and periodic groups
  -  packed and unpacked format
  -  mapping datetime() objects to DATETIME, TIMESTAMP U fields

**adapya 0.7** is the first public release.

