#!/bin/bash

# backup db
DIR="/tmp/ghost_backup"
mkdir -p $DIR
mysqldump -uroot -p ghost_prod > ${DIR}/ghost_prod.sql

# backup content
cp -r /opt/ghost/content ${DIR}

datetime=`date +%Y-%m-%d`
FILE=ghost-backup.tar.gz.${datetime}

tar -cvzf /tmp/$FILE $DIR

/root/s3cmd-1.6.1/s3cmd put /tmp/$FILE s3://cliqrjun/ghost_backup/

rm -rf ${DIR}/content
rm -f /tmp/$FILE




