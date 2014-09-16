#!/bin/bash

VERSION=1.10.0
PKGNAME=tahoe-lafs
SCRIPTBASE=`pwd`

cleanup()
{
    rm *.pkg
}

fetch_src ()
{
    TMPDIR=$SCRIPTBASE
    SRCDIR=`mktemp -d -t ${TMPDIR}`

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

    # create component pkg
    pkgbuild --root osx-pkg \
        --identifier com.leastauthority.tahoe \
        --version $VERSION \
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
