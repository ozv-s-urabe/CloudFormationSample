import boto3
import os
import logging
from holiday import holiday

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

TAG_KEY = os.environ['TagKey']
TAG_VALUE = os.environ['TagValue']
AUTO_SCALING_WAKE_MIN_SIZE = int(os.environ['AutoScalingWakeMinSize'])
AUTO_SCALING_WAKE_MAX_SIZE = int(os.environ['AutoScalingWakeMaxSize'])
AUTO_SCALING_WAKE_DESIRED_CAPACITY = int(os.environ['AutoScalingWakeDesiredCapacity'])
AUTO_SCALING_SLEEP_MIN_SIZE = int(os.environ['AutoScalingSleepMinSize'])
AUTO_SCALING_SLEEP_MAX_SIZE = int(os.environ['AutoScalingSleepMaxSize'])
AUTO_SCALING_SLEEP_DESIRED_CAPACITY = int(os.environ['AutoScalingSleepDesiredCapacity'])
EC2 = boto3.resource('ec2')
RDS = boto3.client('rds')
AutoScaling = boto3.client('autoscaling')

def get_target_ec2_instances():
    filters = [{
        'Name': 'tag:' + TAG_KEY,
        'Values': [TAG_VALUE]
    }]
    return EC2.instances.filter(Filters=filters)

def get_target_autoscaling_groups():
    groups = AutoScaling.describe_auto_scaling_groups()

    results = []
    for group in groups['AutoScalingGroups']:
        tags = group.get('Tags')
        for tag in tags:
            if tag.get('Key') == TAG_KEY and tag.get('Value') == TAG_VALUE:
                results.append(group.get('AutoScalingGroupName'))

    return results

def get_target_rds_instances():
    instances = RDS.describe_db_instances()
    return [
        i for i in instances['DBInstances']
        for tag in RDS.list_tags_for_resource(ResourceName=i['DBInstanceArn'])['TagList']
        if tag['Key'] == TAG_KEY and tag['Value'] == TAG_VALUE
    ]

def schedule_autoscaling(event):
    groups = get_target_autoscaling_groups()
    for group in groups:
        logger.info("Target Autoscaling Group: " + group)
        if [ r for r in event.get('resources') if r.count('StartScheduledRule') ]:
            logger.info('Wake AutoScaling')
            logger.info(AutoScaling.update_auto_scaling_group(
                AutoScalingGroupName=group,
                MinSize=AUTO_SCALING_WAKE_MIN_SIZE,
                MaxSize=AUTO_SCALING_WAKE_MAX_SIZE,
                DesiredCapacity=AUTO_SCALING_WAKE_DESIRED_CAPACITY
            ))
        elif [ r for r in event.get('resources') if r.count('StopScheduledRule') ]:
            logger.info('Sleep AutoScaling')
            logger.info(AutoScaling.update_auto_scaling_group(
                AutoScalingGroupName=group,
                MinSize=AUTO_SCALING_SLEEP_MIN_SIZE,
                MaxSize=AUTO_SCALING_SLEEP_MAX_SIZE,
                DesiredCapacity=AUTO_SCALING_SLEEP_DESIRED_CAPACITY
            ))


def schedule_ec2(event):
    ec2_instances = get_target_ec2_instances()
    logger.info("Target EC2 instances: \n%s" % str(
        [(i.id, tag['Value']) for i in ec2_instances for tag in i.tags if tag.get('Key')=='Name']
    ))

    if [ r for r in event.get('resources') if r.count('StartScheduledRule') ]:
        logger.info('Start EC2 instances')
        logger.info(ec2_instances.start())
    elif [ r for r in event.get('resources') if r.count('StopScheduledRule') ]:
        logger.info('Stop EC2 instances')
        logger.info(ec2_instances.stop())


def schedule_rds(event):
    rds_instances = get_target_rds_instances()
    logger.info("Target RDS instances: \n%s" % str(
        [(i['DBInstanceIdentifier']) for i in rds_instances]
    ))

    if [ r for r in event.get('resources') if r.count('StartScheduledRule') ]:
        logger.info('Start RDS instances')
        for instance in rds_instances:
            if instance['DBInstanceStatus'] == 'stopped':
                logger.info(RDS.start_db_instance(DBInstanceIdentifier=instance['DBInstanceIdentifier']))
            else:
                logger.info('{} status is not "stopped"'.format(instance['DBInstanceIdentifier']))
    elif [ r for r in event.get('resources') if r.count('StopScheduledRule') ]:
        logger.info('Stop RDS instances')
        for instance in rds_instances:
            if instance['DBInstanceStatus'] == 'available':
                logger.info(RDS.stop_db_instance(DBInstanceIdentifier=instance['DBInstanceIdentifier']))
            else:
                logger.info('{} status is not "available"'.format(instance['DBInstanceIdentifier']))


def lambda_handler(event, context):
    logger.info('Started')

    if [ r for r in event.get('resources') if r.count('StartScheduledRule') ]:
        if holiday.is_holiday() == True:
            logger.info('Today is Holiday. Ended.')
            return 0

    schedule_autoscaling(event)
    schedule_ec2(event)
    schedule_rds(event)

    logger.info('Complete')
