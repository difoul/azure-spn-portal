I want to build SPN Self-Service Portal.

## What it does
The application allows all Azure users  to create and configure service principals in a self-service mode.

## Target users
All Azure users

## Stack
Azure
Terraform for Infra As Code
Python for the code
Azure native databases

## Core features (must have) 
- Create and manage service principals in self-service mode
- Authentication and authorization using EntraID


## Nice to have
- Web console


## Requirements
- Login using EntraID
- The requestor is the owner of the Service Principal
- The owner can specify another owner
- The owner can change the configuration of the Service Principal (Renew secret, Redirect URIs ...)
- Each service principal can have only 2 secrets
- Do not allow duplicate names
- Auditable

## Constraints
- Cost-efficient.

Please ask me clarifying questions before doing anything.