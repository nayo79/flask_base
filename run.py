#!/usr/bin/env python
# coding: utf-8

from app import app

#app.testing = False
app.debug = True

app.run(host="0.0.0.0", port=9999)

