#!/bin/bash
egrep -o '"url":([^,]*),' $1 | cut -d ':' -f 2- | cut -d '"' -f 2
