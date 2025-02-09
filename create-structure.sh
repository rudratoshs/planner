#!/bin/bash

# Create directory structure and files
mkdir -p user-service/{src/{api/{routes,middleware,dependencies},core/{models,schemas,services},config,db/migrations,utils},prisma}

# Create all the files
touch user-service/src/__init__.py \
      user-service/src/api/__init__.py \
      user-service/src/api/routes/{__init__,auth,users}.py \
      user-service/src/api/middleware/{__init__,auth,validation}.py \
      user-service/src/api/dependencies/{__init__,database}.py \
      user-service/src/core/__init__.py \
      user-service/src/core/models/{__init__,user,session,password_reset}.py \
      user-service/src/core/schemas/{__init__,user,auth,session}.py \
      user-service/src/core/services/{__init__,user_service,auth_service}.py \
      user-service/src/config/{__init__,settings}.py \
      user-service/src/db/{__init__,session}.py \
      user-service/src/db/migrations/initial_migration.py \
      user-service/src/utils/{__init__,security,response}.py \
      user-service/src/main.py \
      user-service/src/pyproject.toml \
      user-service/prisma/{schema.prisma,seed.py} \
      user-service/{Dockerfile,docker-compose.yml,.env,.gitignore,requirements.txt,README.md,setup.py}

echo "Project structure created successfully!"
