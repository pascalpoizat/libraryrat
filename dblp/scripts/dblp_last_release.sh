#!/bin/bash

curl -s https://dblp.org/xml/release/ | egrep -o '"dblp(.)*.xml.gz"' | cut -d '"' -f 2 | cut -d '.' -f 1 | sort -r | head -n 1
