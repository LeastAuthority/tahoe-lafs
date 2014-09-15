#!/bin/bash

VERSION=1.10.0
PKGNAME=allmydata-tahoe
SCRIPTBASE=`pwd`

cleanup()
{
    rm *.pkg
}

fetch_src ()
{
    tempfoo=`basename $(pwd)`
    TMPDIR=$SCRIPTBASE
    SRCDIR=`mktemp -d -t ${tempfoo}`

    echo "fetching the repository ..."
    wget https://tahoe-lafs.org/source/tahoe-lafs/releases/$PKGNAME-$VERSION.zip -O $SRCDIR/$PKGNAME-$VERSION.zip || exit 1
}

unzip_src()
{
    CURDIR=`pwd`
    cd $SRCDIR
    unzip $PKGNAME-$VERSION.zip    
}

build_src()
{
    cd $PKGNAME-$VERSION
    python setup.py build
}

create_pkg()
{
    cd $SRCDIR
    mkdir osx-pkg
    cp -r $PKGNAME-$VERSION/* osx-pkg/
    cp $SCRIPTBASE/tahoe osx-pkg/

    # create component pkg
    pkgbuild --root osx-pkg \
        --identifier com.leastauthority.tahoe \
        --version 1.10.0 \
        --ownership recommended \
        --install-location /Applications/tahoe.app \
        --scripts $SCRIPTBASE/scripts \
        $SCRIPTBASE/$PKGNAME.pkg

    # create product archive.
    cd $SCRIPTBASE
    productbuild --distribution $SCRIPTBASE/Distribution.xml \
        --package-path . \
        $SCRIPTBASE/Installer.pkg
}

cleanup
fetch_src
unzip_src
build_src
create_pkg
