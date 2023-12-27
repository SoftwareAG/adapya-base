"""
adapya.base.future - Avoid Python FutureWarnings
================================================

"""
import os
def getpid():
    return ((os.getpid() << 16) & 0xffff0000)

#  Copyright 2004-2023 Software AG
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#  $Date: 2016-03-01 17:57:13 +0100 (Tue, 01 Mar 2016) $
#  $Rev: 657 $


