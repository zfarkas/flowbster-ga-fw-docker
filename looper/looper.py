import yaml
import os, sys, stat
from flask import Flask, request, abort, jsonify
import logging as log
import requests
import uuid

DEF_HOST = '0.0.0.0'
DEF_PORT = 6000
DEF_RESDIR = '/tmp/ga_results'
DEF_ROUTEPATH = "/flowbster"
DEF_LOGLEVEL = log.DEBUG
DEF_LOGFORMAT = '%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'

TARGET_IP = '127.0.0.1'

def checkloop(f):
    with open(f) as content:
        value = int(content.read())
        if value == 1:
            log.info('FINISHED!!!')
        else:
            yaml_id = str(uuid.uuid4())
            yaml_data = """
            wfid: %s
            inputs:
                -
                    name: input-data.txt
                    post_file: input-data.txt
            """ % yaml_data
            files = {}
            files["input-data.txt"] = open(f, "rb")
            files[yaml_id] = yaml_data
            global TARGET_IP
            requests.post("http://%s:5000/flowbster" % TARGET_IP, files=files, params=payload)

def create_dir(path):
    if not os.path.exists(path): os.makedirs(path)

def gen_filename_by_index(name,indexlist):
    filename = name
    for i in indexlist:
        filename = filename + "_" + str(i)
    return filename

def create_input_files(confjob,directory):
    for d in confjob['inputs']:
        log.debug("- indexes: normal: "+str(d['index'])+" list: "+str(d['index_list']))
        filename = gen_filename_by_index(d['name'],d['index_list'])
        #filename = d['name']+"_"+str(d['index'])
        log.debug("- file to save: \""+filename+"\"")
        if os.path.exists(os.path.join(directory,filename)):
            log.warning("- file \""+filename+"\" already exists! Renaming...")
            ind = 1
            while os.path.exists(os.path.join(directory,filename+"."+str(ind))):
                ind+=1
            filename = filename+"."+str(ind)
        f = request.files[d['name']]
        target = os.path.join(directory, filename)
        f.save(os.path.join(directory, filename))
        checkloop(os.path.join(directory, filename))
        log.debug("- file saved as \""+filename+"\"")

def deploy(confjob):
    wfidstr = confjob['wfid']
    log.debug("- wfid: "+wfidstr)

    wfiddir = os.path.join(DEF_RESDIR,wfidstr)
    if os.path.exists(wfiddir):
        log.debug("- directory already exists...")
    else:
        create_dir(wfiddir)
    create_input_files(confjob,wfiddir)
    log.info("File collection finished.")



log.basicConfig(stream=sys.stdout, level=DEF_LOGLEVEL, format=DEF_LOGFORMAT)
app = Flask(__name__)

@app.route(DEF_ROUTEPATH, methods=['POST'])
def receive():
    log.info("New file(s) arrived.")
    yaml_param = request.args.get('yaml', '')
    rdata = request.files[yaml_param].read()
    confjob = yaml.load(rdata)
    deploy(confjob)
    return "ok"

@app.route("/setup", methods=["POST"])
def setup():
    log.info("Setup request arrived...")
    ip = request.form.get('ip', None)
    if ip == None:
        return jsonify({'message': 'please specify a value for the "ip" form key'}), 400
    else:
        global TARGET_IP
        log.info('Target IP changed from %s to %s' % (TARGET_IP, ip))
        TARGET_IP = ip
        return jsonify({'message': 'target IP successfully set to "%s"' % TARGET_IP}), 200


log.info("Storing results into directory: "+DEF_RESDIR)
log.info("Listening on port "+str(DEF_PORT)+", under url \""+DEF_ROUTEPATH+"\"")

if __name__ == "__main__":
    app.run(host=DEF_HOST, port=DEF_PORT)
