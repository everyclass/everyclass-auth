#!/usr/bin/env bash
docker build . -t everyclass-auth:$(git describe --tag)