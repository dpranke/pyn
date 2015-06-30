#!/bin/bash
# Copyright 2014 Dirk Pranke. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

if readlink $0 > /dev/null
then
    SCRIPTDIR=$(dirname $(readlink $0))
else
    pushd $(dirname $0) > /dev/null
    SCRIPTDIR=$(pwd -P)
    popd > /dev/null
fi
python -B $SCRIPTDIR/main.py $@
