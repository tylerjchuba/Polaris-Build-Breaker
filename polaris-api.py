import argparse
import json
import re
import urllib.request
import urllib.parse
import requests

parser = argparse.ArgumentParser(description='Get Polaris job data')
job_group = parser.add_mutually_exclusive_group()
parser.add_argument('-t', '--token',type=str, help='Polaris personal access token')
job_group.add_argument('-j', '--job', type=str, help='Polaris job id')
parser.add_argument('-u', '--base_url', type=str,
                    default='sipse.polaris.synopsys.com/',
                    help='The full Polaris instance domain. '
                         'Default: polaris.synopsys.com')
parser.add_argument('-v', '--verbose', action='store_true',
                    help='Prints API results output to STDOUT')

args = parser.parse_args()




access_token = args.token
base_url = 'https://' + args.base_url.rstrip('/')

API_AUTH = base_url + '/api/auth/authenticate'
API_JOBS = base_url + "/api/common/v0/projects?page%5Blimit%5D=100"
API_ROLLUPS = base_url + "/api/common/v0/branches?page%5Blimit%5D=100"

API_JOB = base_url + '/api/jobs/jobs/'
API_ISSUES = base_url + '/api/query/v0/issues?'
TAXONOMIES = base_url + '/api/taxonomy/v0/taxonomies?page%5Blimit%5D=100'

headers = {'Accept': 'application/json',
           'Content-Type': 'application/x-www-form-urlencoded'}



# Updates headers for requests
def getAuth():
  auth_params = urllib.parse.urlencode({'accesstoken': access_token})
  auth_params = auth_params.encode('ascii')

  r = urllib.request.urlopen(API_AUTH, auth_params).read()

  auth_body = json.loads(r.decode('utf-8'))

  headers['Authorization'] = 'Bearer ' + auth_body['jwt']
  headers['Accept'] = 'application/vnd.api+json'

# Finds the project ID of the given project name paramater
def getProjID(): 
  req = urllib.request.Request(API_JOBS, headers=headers)
  r = urllib.request.urlopen(req).read()

  jobs_body = json.loads(r.decode('utf-8'))

  data = jobs_body['data']
  project_id = ''
  for item in data:
    if item['attributes']['name'] == str(args.job): 
      project_id = item['id']
      return project_id

# Find the branch ID of Polaris 
def getBranchID():
  r_req = urllib.request.Request(API_ROLLUPS, headers=headers)
  r_res = urllib.request.urlopen(r_req).read()
  r_body = json.loads(r_res.decode('utf-8'))
  # if branch ID fails alternate the array position [0] until it does work - untested if this is correct 
  branch_id = r_body['data'][0]['id']
  return branch_id

def getTaxID(): 
  tax_headers = dict(headers) 
  tax_headers['Accept'] = 'application/json'
  tax_headers['Content-type'] = 'application/json'
  #establish session
  req = requests.Request('GET', TAXONOMIES, headers=tax_headers)
  prepared = req.prepare()
  session = requests.session()
  response = session.send(prepared)
  data = json.loads(response.text)
  taxonomy_id = ''
  for item in data['data']:
    if item['taxonomy-type'] == 'severity':
      taxonomy_id = item['id']
      return taxonomy_id


def getHigh(branch_id, taxonomy_id, project_id):
  params = {"branch-id": str(branch_id),
  "filter[issue][status][$eq]":"opened",
  "include[issue][]":["transitions","related-taxa","related-indicators","severity"],
  "filter[issue][taxonomy][id][" + str(taxonomy_id) + "][taxon][$eq]":"high",
  "page[offset]":"0",
  "page[limit]":"25",
  "project-id":str(project_id)}


  params = urllib.parse.urlencode(params)

  req = requests.Request('GET', API_ISSUES + params, headers=headers)
  prepared = req.prepare()
  session = requests.session()
  response = session.send(prepared)
  data = json.loads(response.text)
  return data['meta']['total']

def quitJob(findings):
  print('Found {} high findings'.format(findings))
  if findings != 0:
    exit(1)
  else:
    exit(0) 


getAuth()
taxonomy_id = getTaxID()
branch_id = getBranchID()
project_id = getProjID() 
findings = getHigh(branch_id, taxonomy_id,project_id)
quitJob(findings)