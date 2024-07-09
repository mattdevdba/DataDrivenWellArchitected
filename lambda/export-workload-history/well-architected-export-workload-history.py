import boto3
import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_bucket = os.environ['S3_BUCKET']
s3_key = os.environ['S3_KEY']

#################
# Boto3 Clients #
#################
wa_client = boto3.client('wellarchitected')
s3_client = boto3.client('s3')

##############
# Parameters #
##############
# The maximum number of results the API can return in a list workloads call.
list_workloads_max_results_maximum = 50
# The maximum number of results the API can return in a list answers call.
list_answers_max_results_maximum = 50
# The maximum number of results the API can return in a list milestones call.
list_milestone_max_results_maximum = 50

def get_workload(workload_id):
    workload_result = wa_client.get_workload(WorkloadId=workload_id)
    return (workload_result)

def get_milestone(workload_id, milestone_number):
    milestone = wa_client.get_milestone(WorkloadId=workload_id, MilestoneNumber=milestone_number)['Milestone']
    return milestone

def get_lens_review(workload_id, lens_alias, milestone_number):
    lens = wa_client.get_lens_review(WorkloadId=workload_id, LensAlias=lens_alias, MilestoneNumber=milestone_number)['LensReview']
    return lens

def get_milestones(workload_id):
    milestones = wa_client.list_milestones(
        WorkloadId=workload_id, MaxResults=list_milestone_max_results_maximum
    )['MilestoneSummaries']

    total_milestones = len(milestones)

    # If workload has milestone get them.
    logger.info(f'Workload {workload_id} has {len(milestones)} milestones.')
    if milestones:
        for milestone in milestones:
            milestone['RecordedAt'] = milestone['RecordedAt'].strftime("%Y-%m-%d %H:%M:%S")
            if milestone['MilestoneNumber'] == total_milestones:
                milestone['IsLatest'] = 'Yes'
            else:
                milestone['IsLatest'] = 'No'
    return milestones

def get_answers(WorkloadId,LensAlias,PillarId,MilestoneNumber,MaxResults):
    workload_answers = []
    answers = wa_client.list_answers(
        WorkloadId=WorkloadId,
        LensAlias=LensAlias,
        PillarId=PillarId,
        MilestoneNumber=MilestoneNumber,
        MaxResults=MaxResults
    )
    workload_answers.append(answers['AnswerSummaries'])
    while "NextToken" in answers:
        answers = wa_client.list_answers(
            WorkloadId=WorkloadId,
            LensAlias=LensAlias,
            PillarId=PillarId,
            MilestoneNumber=MilestoneNumber,
            MaxResults=MaxResults,
            NextToken=answers["NextToken"]
        )
        workload_answers.append(answers['AnswerSummaries'])
    logger.info(f'Found {len(answers)} answers for Lens {LensAlias} pillar {PillarId} milestone {MilestoneNumber}')
    #print(workload_answers)
    return workload_answers

def save_to_s3(workload_report_data,workload_id):
    workload = get_workload(workload_id)['Workload']
    workload_name = workload['WorkloadName']
    file_name = workload_id + '-' + workload_name + '.json'

    logger.info(f'Writing JSON object to file://temp/{file_name}.')
    with open('/tmp/'+file_name, 'w') as json_file:
        for x in workload_report_data:
            json_file.writelines(json.dumps(x)+'\n')
    logger.info(f'Writing JSON object to s3://{s3_bucket}/{s3_key}{file_name}.')

    s3_client.upload_file('/tmp/'+file_name, s3_bucket, s3_key+file_name)



def generate_output(question_list):
    output_list=[]
    for item in question_list:
        response = wa_client.get_answer(
            WorkloadId=item['workload_id'],
            LensAlias=item['lens_alias'],
            QuestionId=item['question_id'],
            MilestoneNumber=item['milestone_number']
        )

        milestone=get_milestone(item['workload_id'],item['milestone_number'])
        lens=get_lens_review(item['workload_id'],item['lens_alias'],item['milestone_number'])        #print(response)
        workload = get_workload(response['WorkloadId'])['Workload']
        output = {}
        output['workload_id'] = response['WorkloadId']
        output['workload_arn'] = workload['WorkloadArn']
        output['workload_name'] = workload['WorkloadName']
        output['workload_description'] = workload['Description']
        output['workload_environment'] = workload['Environment']
        output['workload_updated'] = workload['UpdatedAt'].strftime("%Y-%m-%d %H:%M:%S")
        if "AccountIds" in workload:
            output['workload_account_ids'] = workload['AccountIds']
        else:
            output['workload_account_ids'] = "N/A"
        output['workload_aws_regions'] = workload['AwsRegions']
        if 'ReviewOwner' in workload:
            output['workload_review_owner'] = workload['ReviewOwner']
        else:
            output['workload_review_owner'] =""
        if 'IndustryType' in workload:
            output['workload_industry_type'] = workload['IndustryType']
        else:
             output['workload_industry_type'] = "N/A"
        output['workload_improvement_status'] = workload['ImprovementStatus']
        output['workload_tags'] = workload['Tags']
        if 'Product' in workload['Tags']:
            output['tag_product'] = workload['Tags']['Product']
        else:
            output['tag_product'] =""
        if 'ProductFamily' in workload['Tags']:
            output['tag_product_family'] = workload['Tags']['ProductFamily']
        else:
            output['tag_product_family'] =""
        output['milestone_number'] = response['MilestoneNumber']
        output['milestone_name'] = milestone['MilestoneName']
        output['milestone_recorded_at'] = milestone['RecordedAt'].strftime("%Y-%m-%d %H:%M:%S")
        output['milestone_is_latest'] = item['milestone_is_latest']
        output['lens_alias'] = response['LensAlias']
        output['lens_arn'] = response['LensArn']
        output['lens_version'] = lens['LensVersion']
        output['lens_name'] = lens['LensName']
        output['lens_status'] = lens['LensStatus']
        output['lens_updated_at'] = lens['UpdatedAt'].strftime("%Y-%m-%d %H:%M:%S")
        output['question_id'] = response['Answer']['QuestionId']
        output['pillar_id'] = response['Answer']['PillarId']
        output['question_title'] = response['Answer']['QuestionTitle']
        output['question_description'] = response['Answer']['QuestionDescription']
        if "improvement_plan_url" in response['Answer']:
            output['improvement_plan_url'] = response['Answer']['improvement_plan_url']
        else:
            output['improvement_plan_url'] = "N/A"
        output['helpful_resource_url'] = response['Answer']['HelpfulResourceUrl']
        output['selected_choices'] = response['Answer']['SelectedChoices']
        output['risk'] = response['Answer']['Risk']
        if response['Answer']['Risk'] == "HIGH":
            output['risk_high'] = 1
            risk_score = 10
        else:
            output['risk_high'] = 0
        if response['Answer']['Risk'] == "MEDIUM":
            output['risk_medium'] = 1
            risk_score = 5
        else:
            output['risk_medium'] = 0
        if response['Answer']['Risk'] == "NONE":
            output['risk_none'] = 1
            risk_score = 0
        else:
            output['risk_none'] = 0
        if response['Answer']['Risk'] == "NOT_APPLICABLE":
            output['risk_not_applicable'] = 1
            risk_score = 0
        else:
            output['risk_not_applicable'] = 0
        if response['Answer']['Risk'] == "UNANSWERED":
            output['risk_unanswered'] = 1
            risk_score = 3
        else:
            output['risk_unanswered'] = 0
        output['risk_score'] = risk_score
        output['is_applicable'] = response['Answer']['IsApplicable']
        if "Notes" in response['Answer']:
            output['notes'] = response['Answer']['Notes']
        else:
            output['notes'] = "N/A"
        if "Reason" in response['Answer']:
            output['reason'] = response['Answer']['Reason']
        else:
            output['reason'] = "N/A"
        output_list.append(output)
    return output_list

def lambda_handler(event, context):
    workload_id = event['detail']['workload_id']
    logger.info(f'Build JSON object for workload {workload_id}.')
    question_list = []

    milestones = get_milestones(workload_id)

    for milestone in milestones:
        milestone_number = milestone['MilestoneNumber']

        lenses = milestone['WorkloadSummary']['Lenses']
        logger.info(f'Found {len(lenses)} lenses.')
        for lens in lenses:

            lens_review = wa_client.get_lens_review(
                WorkloadId=workload_id,
                LensAlias=lens,
                MilestoneNumber=milestone_number)['LensReview']
            pillars = lens_review['PillarReviewSummaries']
            for pillar in pillars:
                pillar_id=pillar['PillarId']
                #each lens has one or more pillars
                #each pillar has one or more questions and responses
                answers=get_answers(workload_id,lens,pillar_id,milestone_number,list_answers_max_results_maximum)
                answers=answers[0]
                for answer in answers:
                   question = {"workload_id": workload_id, "lens_alias": lens, "milestone_number": milestone_number, "milestone_is_latest":  milestone['IsLatest'], "question_id": answer['QuestionId'], "pillar_id": pillar_id}
                   question_list.append(question)


    workload_report_data=generate_output(question_list)
    save_to_s3(workload_report_data,workload_id)
