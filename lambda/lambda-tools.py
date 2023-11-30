"""
Usage

cd /Users/tony/GitHub/westernchances/lambda

Add common and common files into each needed function
ln -s ../common/utils.py utils.py

Can also link from rosella/lambda/common

python3 lambda-tools.py --region=ap-southeast-4 --client=example 
python3 lambda-tools.py --region=ap-southeast-4 --client=example create --function=test --role-arn=arn:aws:iam::nnnnnnnnnnnn:role/name
python3 lambda-tools.py --region=ap-southeast-4 --client=example upload --function=test
python3 lambda-tools.py --region=ap-southeast-4 --client=example sync
python3 lambda-tools.py --region=ap-southeast-4 --client=example sync --all

References
https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda/client/create_function.html
"""

import argparse
import datetime
from glob import glob
import json
import os
from pathlib import Path
import sys
import time
import zipfile

import boto3
from botocore.exceptions import ClientError, ProfileNotFound


def create_zip_file(args, lambda_session, function_name=None, verbose=True):
    zip_name = function_name + '.zip'

    print('creating zip file', zip_name)

    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
        for folder_name, subfolders, filenames in os.walk(function_name):
            for filename in filenames:
                if filename == '.DS_Store':
                    continue

                file_path = os.path.join(folder_name, filename)

                if verbose:
                    print('  adding', file_path)

                zip_ref.write(file_path, arcname=os.path.relpath(file_path, function_name))

    zip_ref.close()


def create_and_upload_function(args, lambda_session, function_name=None):
    zip_name = function_name + '.zip'

    with open(zip_name, 'rb') as f:
        zip_bytes = f.read()

        try:
            response = lambda_session.create_function(
                FunctionName=function_name,
                Runtime=args.runtime,
                Role=args.role_arn,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_bytes},
                # Description='',
                Timeout=30,
                MemorySize=256,
                Publish=True,
                PackageType='Zip',
                Environment={
                    'Variables': {
                        'created_source': str(Path(zip_name).resolve()),
                        'created_script': 'lambda-tools.py',
                        'created_date':   datetime.datetime.now().isoformat(),
                    }
                },
                # TracingConfig={
                #     'Mode': 'Active'|'PassThrough'
                # },
                # Tags={
                #     'string': 'string'
                # },
                # Layers=[
                #     'string',
                # ],
                Architectures=[args.architecture],
                # EphemeralStorage={
                #     'Size': 123
                # },
                # LoggingConfig={
                #     'LogFormat': 'JSON'|'Text',
                #     'ApplicationLogLevel': 'TRACE'|'DEBUG'|'INFO'|'WARN'|'ERROR'|'FATAL',
                #     'SystemLogLevel': 'DEBUG'|'INFO'|'WARN',
                #     'LogGroup': 'string'
                # }
                )
        except lambda_session.exceptions.ResourceConflictException as e:
            sys.exit(f'*** {e}')

        function_name    = response.get('FunctionName')
        function_arn     = response.get('FunctionArn')
        function_runtime = response.get('Runtime')
        
        # print(json.dumps(response, indent=2))
        print(f'lambda function {function_name} created with {function_arn}')


def upload_function(args, lambda_session, function_name=None):
    zip_name = function_name + '.zip'

    with open(zip_name, 'rb') as f:
        zip_bytes = f.read()

        try:
            response = lambda_session.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_bytes,
                Publish=True,
                Architectures=[args.architecture],
            )

            print(f'lambda function {function_name} uploaded\n')

        except lambda_session.exceptions.ResourceConflictException as e:
            sys.exit(f'*** Update failed because an update is in progress for {function_name}')


def list_command(args, lambda_session):
    response = lambda_session.list_functions()
    # print(json.dumps(response, indent=2))

    print(f'List all functions in region {args.region}\n')

    for function in response.get('Functions'):
        function_name    = function.get('FunctionName')
        function_runtime = function.get('Runtime')
        function_version = function.get('Version')

        print(f'function {function_name=} {function_runtime=} {function_version=}')


def create_command(args, lambda_session):
    create_zip_file(args, lambda_session, function_name=args.function)
    create_and_upload_function(args, lambda_session, function_name=args.function)


def upload_command(args, lambda_session):
    create_zip_file(args, lambda_session, function_name=args.function)
    upload_function(args, lambda_session, function_name=args.function)


def sync_command(args, lambda_session):
    print(f'Sync lambda function changes in region {args.region}\n')

    something_updated = False

    for folder_name in glob('*'):
        if '.' in folder_name:
            continue

        if folder_name == 'common':
            continue

        lambda_name = Path(folder_name).name

        if args.all:
            print(f'examining lambda {lambda_name}')

        files_to_update = []

        for subfolder, subsubfolders, filenames in os.walk(folder_name):
            updated = False

            for filename in filenames:
                if filename == '.DS_Store':
                    continue

                file_path     = os.path.join(subfolder, filename)
                modified_time = os.path.getmtime(file_path)

                if args.all:
                    updated = True
                    something_updated = True
                    print(f'  updating {file_path}')

                elif time.time() - modified_time < args.sync_wait:
                    updated = True
                    something_updated = True
                    print(f'updating {file_path}')

        if updated:
            pass
            create_zip_file(args, lambda_session, function_name=lambda_name, verbose=False)
            upload_function(args, lambda_session, function_name=lambda_name)

    if not something_updated:
        print('nothing to do')


def main(args):
    try:
        session        = boto3.Session(profile_name=args.client, region_name=args.region)
        lambda_session = session.client('lambda')

    except ProfileNotFound as e:
        sys.exit('aws profile not found (--client)')

    if args.command == 'list':
        list_command(args, lambda_session)

    elif args.command == 'create':
        create_command(args, lambda_session)

    elif args.command == 'upload':
        upload_command(args, lambda_session)

    elif args.command == 'sync':
        sync_command(args, lambda_session)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--client')
    parser.add_argument('-r', '--region')
    parser.add_argument('-f', '--function')
    parser.add_argument('-a', '--architecture', default='arm64', nargs='?', choices=['x86_64', 'arm64'])
    parser.add_argument(      '--runtime',      default='python3.12', nargs='?', choices=['python3.10', 'python3.11', 'python3.12'])
    parser.add_argument(      '--role-arn')
    parser.add_argument('-w', '--sync-wait',    default=600, type=int)
    parser.add_argument(      '--all',          action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument('command',              default='list', nargs='?', choices=['list', 'upload', 'create', 'sync'])

    args = parser.parse_args()

    main(args)
