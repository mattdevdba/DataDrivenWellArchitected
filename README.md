# Data Driven Well Architected

Code and supporting resources from public talk on Data Driven AWS Well Architected. First presneted in full at AWS Summit New York 2024 (session code DEV203).

## Talk Abstract

In this session I’ll be talking about how you can use data from the Well Architected (WA) Tool to drive improvements in software development.

I will demo how to extract data from the WA tool and then show how I've used QuickSight to build dashboards that profile risks across an organisations architecture.

I’ll show how you can improve design review transparency and tailor well architected to your organisation or industry specific needs with custom lenses.

Above all I will show a data driven approach using the Generative AI features in Q for QuickSight to ask questions around architure risks and identify trends for improvements across a software development organisation.

## Architecture Diagram for Solution

![DEV203 - Data Driven Well Architected - AWS NYC Summit 2024 - Architecture Diagram.png](https://github.com/mattdevdba/DataDrivenWellArchitected/blob/main/DEV203%20-%20Data%20Driven%20Well%20Architected%20-%20AWS%20NYC%20Summit%202024%20-%20Architecture%20Diagram.png)

## Lambda Fucntions

### get-workloads

This Lambda fucntion should be executed on a schedule via Event Bridge Rule.
For example run every day at 8AM.
* name: well-architected-schedule
* Schedule expression: cron(0 08 * * ? *)

### export-workload-history

This lambda fucntion should be executed via an Event Bridge Rule:
* Event bus: default
* Event pattern:
```
{
  "detail-type": [
    "well-architected-workload"
  ]
}
```
It requires the following environmnet variables to be set.
* S3_BUCKET : the-name-of-your-s3-bucket
* S3_KEY : folder/





