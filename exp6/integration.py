"""
Note that I call a workflow from a workflow. 
I can't call transactions from a step, thus the 2nd workflow.
"""

import logging
import os
import sys
import time
from ast import List

import boto3
from dbos import DBOS, DBOSConfiguredInstance, Queue, WorkflowHandle
from pythonjsonlogger.json import JsonFormatter

log_handler = logging.StreamHandler(sys.stdout)
formatter = JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={"levelname": "severity", "asctime": "timestamp"},
)
log_handler.setFormatter(formatter)

DBOS.logger.handlers = [log_handler]

DBOS()
DBOS.launch()

# it may not start more than 50 functions in 10 seconds
queue = Queue("integration_queue", concurrency=10, limiter={"limit": 50, "period": 10})

MY_BUCKET = "ricardo-exp-650794013116-us-east-1"


class S3FetcherStatic:
    client_s3 = boto3.client(
        "s3",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )
    bucket_name = MY_BUCKET

    @staticmethod
    @DBOS.workflow()
    def list_files():
        handles: List[WorkflowHandle] = []
        paginator = S3FetcherStatic.client_s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=S3FetcherStatic.bucket_name):
            DBOS.logger.debug(
                dict(
                    message="Enqueuing",
                    workflow_id=DBOS.workflow_id,
                    key_count=page["KeyCount"],
                    max_keys=page["MaxKeys"],
                    is_truncated=page["IsTruncated"],
                )
            )
            handle: WorkflowHandle = queue.enqueue(S3FetcherStatic._list_page, page)
            handles.append(handle)
        for handle in handles:
            res = handle.get_result()
            DBOS.logger.debug(
                dict(
                    message="Handle Result",
                    workflow_id=handle.workflow_id,
                    result=res.get("message"),
                )
            )

    @staticmethod
    @DBOS.step()
    def _list_page(page):
        for obj in page["Contents"]:
            DBOS.logger.info(dict(message="list_files", key=obj["Key"]))
        return dict(message="Page listed", page=page)


# it does not work self.client_s3 is not pickable
@DBOS.dbos_class()
class S3FetcherDoesNotWork(DBOSConfiguredInstance):
    def __init__(self, bucket_name):
        self.client_s3 = boto3.client(
            "s3",
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )
        self.bucket_name = bucket_name
        DBOSConfiguredInstance.__init__(self, "S3Fetcher")

    @DBOS.workflow()
    def list_files(self):
        handles: List[WorkflowHandle] = []
        paginator = self.client_s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket_name):
            DBOS.logger.debug(
                dict(
                    message="Enqueuing",
                    workflow_id=DBOS.workflow_id,
                    key_count=page["KeyCount"],
                    max_keys=page["MaxKeys"],
                    is_truncated=page["IsTruncated"],
                )
            )
            handle: WorkflowHandle = queue.enqueue(self._list_page, page)
            handles.append(handle)
        for handle in handles:
            res = handle.get_result()
            DBOS.logger.debug(
                dict(
                    message="Handle Result",
                    workflow_id=handle.workflow_id,
                    result=res.get("message"),
                )
            )

    @DBOS.step()
    def _list_page(self, page):
        for obj in page["Contents"]:
            DBOS.logger.info(dict(message="list_files", key=obj["Key"]))
        return dict(message="Page listed", page=page)


# Main workflow
@DBOS.workflow()
def process():
    DBOS.logger.info(dict(message="Starting Workflow", workflow_id=DBOS.workflow_id))
    handles = []
    handle: WorkflowHandle = DBOS.start_workflow(S3FetcherStatic.list_files)
    # start here other workflows: lis 1users, list groups, etc

    # s3_fecher = S3FetcherDoesNotWork(MY_BUCKET)
    # handle: WorkflowHandle = DBOS.start_workflow(s3_fecher.list_files)

    handles.append(handle)
    for handle in handles:
        res = handle.get_result()
        DBOS.logger.info(
            dict(message="Workflow Result", workflow_id=handle.workflow_id, result=res)
        )
    DBOS.logger.info(dict(message="Finished Workflow", workflow_id=DBOS.workflow_id))


if __name__ == "__main__":
    DBOS.logger.info(dict(message="Starting Main", timestamp=time.time()))
    process()
    DBOS.logger.info(dict(message="Finished Main", timestamp=time.time()))
    DBOS.destroy()
    sys.exit(0)
