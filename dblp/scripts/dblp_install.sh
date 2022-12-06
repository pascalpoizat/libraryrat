#!/bin/sh

DBLP_DTD_VERSION="2019-11-22"
DBLP_RELEASE="2022-12-01"
JAR_FILE="mmdb-2019-04-29.jar"
FILE_DEST="../app/src/main/resources/"
JAR_DEST="../app/libs/"

wget https://dblp.org/src/${JAR_FILE} \
	https://dblp.org/xml/release/dblp-${DBLP_RELEASE}.xml.gz \
	https://dblp.org/xml/release/dblp-${DBLP_DTD_VERSION}.dtd

gunzip dblp-${DBLP_RELEASE}.xml.gz

mkdir -p ${JAR_DEST}
mv -f ${JAR_FILE} ${JAR_DEST}
mv -f dblp-${DBLP_RELEASE}.xml ${FILE_DEST}
mv -f dblp-${DBLP_DTD_VERSION}.dtd ${FILE_DEST}
