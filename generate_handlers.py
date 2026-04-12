"""
One-time script to generate stub handler files for all new domains.
Run once, then delete this file.
"""
import os

HANDLERS_DIR = os.path.join(os.path.dirname(__file__), "handlers")

# (domain, prefix, api_base, [(action, intent_suffix, description, param_extraction, dry_msg, sim_extras)])
DOMAINS = [
    ("stream", "str", "/kinesis/v1/streams", [
        ("create", "create", "data stream", 'name=params.get("name",_fake_id())\n    shards=params.get("shards","4")', "Would create stream '{name}' with {shards} shards", '"name":name,"shards":shards,"stream_arn":f"arn:aws:kinesis:us-east-1:123456:stream/{name}"'),
        ("delete", "delete", "data stream", 'name=params.get("name","unknown")', "Would delete stream '{name}'", ''),
        ("scale", "scale", "stream shards", 'name=params.get("name","unknown")\n    shards=params.get("shards","")', "Would scale stream '{name}' to {shards} shards", '"shards":shards'),
        ("status", "status", "data stream", 'name=params.get("name","unknown")', "Would fetch status for stream '{name}'", '"state":"ACTIVE","open_shards":random.randint(1,16),"incoming_records":f"{random.randint(100,10000)}/s"'),
    ]),
    ("serverless", "fn", "/lambda/v1/functions", [
        ("deploy", "deploy", "function", 'name=params.get("name",_fake_id())\n    runtime=params.get("runtime","python3.12")\n    memory=params.get("memory","256")', "Would deploy function '{name}' (runtime={runtime}, memory={memory}MB)", '"name":name,"runtime":runtime,"memory":memory,"function_arn":f"arn:aws:lambda:us-east-1:123456:function:{name}"'),
        ("delete", "delete", "function", 'name=params.get("name","unknown")', "Would delete function '{name}'", ''),
        ("invoke", "invoke", "function", 'name=params.get("name","unknown")', "Would invoke function '{name}'", '"request_id":_fake_id("req"),"duration_ms":random.randint(50,3000),"status_code":200'),
        ("update_config", "update_config", "function config", 'name=params.get("name","unknown")', "Would update config for function '{name}'", ''),
        ("status", "status", "function", 'name=params.get("name","unknown")', "Would fetch status for function '{name}'", '"state":"Active","runtime":params.get("runtime","python3.12"),"invocations_24h":random.randint(100,100000)'),
    ]),
    ("container", "img", "/ecr/v1/images", [
        ("push", "push", "image to registry", 'image=params.get("image",params.get("name","unknown"))', "Would push image '{image}' to registry", '"image":image,"digest":f"sha256:{_fake_id(\"d\")}"'),
        ("pull", "pull", "image from registry", 'image=params.get("image",params.get("name","unknown"))', "Would pull image '{image}' from registry", '"image":image'),
        ("delete", "delete", "image from registry", 'image=params.get("image",params.get("name","unknown"))', "Would delete image '{image}' from registry", ''),
        ("list", "list", "images in registry", 'registry=params.get("registry",params.get("name","default"))', "Would list images in registry '{registry}'", '"count":random.randint(5,50)'),
        ("status", "status", "container registry", 'name=params.get("name","default")', "Would fetch status for registry '{name}'", '"images":random.randint(10,200),"size_gb":round(random.uniform(1,100),1)'),
    ]),
    ("iam", "role", "/iam/v1", [
        ("create_role", "create_role", "IAM role", 'name=params.get("name",_fake_id())', "Would create IAM role '{name}'", '"name":name,"role_arn":f"arn:aws:iam::123456:role/{name}"'),
        ("delete_role", "delete_role", "IAM role", 'name=params.get("name","unknown")', "Would delete IAM role '{name}'", ''),
        ("attach_policy", "attach_policy", "policy", 'role=params.get("role",params.get("name","unknown"))\n    policy=params.get("policy","unknown")', "Would attach policy '{policy}' to role '{role}'", '"role":role,"policy":policy'),
        ("create_user", "create_user", "IAM user", 'name=params.get("name",_fake_id("user"))', "Would create IAM user '{name}'", '"name":name,"user_arn":f"arn:aws:iam::123456:user/{name}"'),
        ("status", "status", "IAM", 'name=params.get("name","")', "Would fetch IAM status", '"roles":random.randint(5,50),"users":random.randint(3,30),"policies":random.randint(10,100)'),
    ]),
    ("vpc", "vpc", "/vpc/v1", [
        ("create", "create", "VPC", 'name=params.get("name",_fake_id())\n    cidr=params.get("cidr","10.0.0.0/16")', "Would create VPC '{name}' with CIDR {cidr}", '"name":name,"vpc_id":_fake_id("vpc"),"cidr":cidr'),
        ("delete", "delete", "VPC", 'name=params.get("name","unknown")', "Would delete VPC '{name}'", ''),
        ("peer", "peer", "VPC peering", 'source=params.get("source",params.get("name","unknown"))\n    target=params.get("target","unknown")', "Would peer VPC '{source}' with '{target}'", '"peering_id":_fake_id("pcx"),"source":source,"target":target'),
        ("status", "status", "VPC", 'name=params.get("name","unknown")', "Would fetch status for VPC '{name}'", '"state":"available","subnets":random.randint(2,8),"route_tables":random.randint(1,4)'),
    ]),
    ("subnet", "subnet", "/vpc/v1/subnets", [
        ("create", "create", "subnet", 'name=params.get("name",_fake_id())\n    cidr=params.get("cidr","10.0.1.0/24")', "Would create subnet '{name}' with CIDR {cidr}", '"name":name,"subnet_id":_fake_id("subnet"),"cidr":cidr'),
        ("delete", "delete", "subnet", 'name=params.get("name","unknown")', "Would delete subnet '{name}'", ''),
        ("status", "status", "subnet", 'name=params.get("name","unknown")', "Would fetch status for subnet '{name}'", '"state":"available","available_ips":random.randint(10,250)'),
    ]),
    ("vpn", "vpn", "/vpn/v1/connections", [
        ("create", "create", "VPN connection", 'name=params.get("name",_fake_id())', "Would create VPN connection '{name}'", '"name":name,"vpn_id":_fake_id("vpn"),"state":"pending"'),
        ("delete", "delete", "VPN connection", 'name=params.get("name","unknown")', "Would delete VPN connection '{name}'", ''),
        ("status", "status", "VPN connection", 'name=params.get("name","unknown")', "Would fetch status for VPN '{name}'", '"state":"available","tunnels_up":random.randint(1,2)'),
    ]),
    ("nat", "nat", "/vpc/v1/nat-gateways", [
        ("provision", "provision", "NAT gateway", 'name=params.get("name",_fake_id())\n    subnet=params.get("subnet","unknown")', "Would provision NAT gateway '{name}' in subnet '{subnet}'", '"name":name,"nat_id":_fake_id("nat"),"subnet":subnet'),
        ("delete", "delete", "NAT gateway", 'name=params.get("name","unknown")', "Would delete NAT gateway '{name}'", ''),
        ("status", "status", "NAT gateway", 'name=params.get("name","unknown")', "Would fetch status for NAT gateway '{name}'", '"state":"available","bytes_processed":random.randint(1000000,9999999999)'),
    ]),
    ("waf", "waf", "/waf/v1", [
        ("create", "create", "WAF", 'name=params.get("name",_fake_id())', "Would create WAF '{name}'", '"name":name,"waf_id":_fake_id("waf"),"rules_count":0'),
        ("delete", "delete", "WAF", 'name=params.get("name","unknown")', "Would delete WAF '{name}'", ''),
        ("update_rules", "update_rules", "WAF rules", 'name=params.get("name","unknown")', "Would update rules on WAF '{name}'", '"rules_count":random.randint(3,20)'),
        ("status", "status", "WAF", 'name=params.get("name","unknown")', "Would fetch status for WAF '{name}'", '"state":"active","blocked_requests_24h":random.randint(100,50000),"rules_count":random.randint(3,20)'),
    ]),
    ("ddos", "ddos", "/shield/v1", [
        ("enable", "enable", "DDoS protection", 'name=params.get("name","unknown")\n    tier=params.get("tier","standard")', "Would enable {tier} DDoS protection on '{name}'", '"name":name,"tier":tier,"protection_id":_fake_id("ddos")'),
        ("disable", "disable", "DDoS protection", 'name=params.get("name","unknown")', "Would disable DDoS protection on '{name}'", ''),
        ("status", "status", "DDoS protection", 'name=params.get("name","unknown")', "Would fetch DDoS protection status for '{name}'", '"protected":True,"attacks_mitigated_30d":random.randint(0,50)'),
    ]),
    ("cdn", "cdn", "/cloudfront/v1/distributions", [
        ("create", "create", "CDN distribution", 'name=params.get("name",_fake_id())\n    origin=params.get("origin","")', "Would create CDN distribution '{name}' with origin '{origin}'", '"name":name,"distribution_id":_fake_id("E"),"domain_name":f"{_fake_id(\"d\")}.cloudfront.net"'),
        ("delete", "delete", "CDN distribution", 'name=params.get("name","unknown")', "Would delete CDN distribution '{name}'", ''),
        ("invalidate", "invalidate", "CDN cache", 'name=params.get("name","unknown")\n    path=params.get("path","/*")', "Would invalidate CDN cache for '{name}' path={path}", '"invalidation_id":_fake_id("inv"),"path":path'),
        ("status", "status", "CDN distribution", 'name=params.get("name","unknown")', "Would fetch status for CDN '{name}'", '"state":"Deployed","hit_rate":f"{random.randint(70,99)}%","requests_24h":random.randint(1000,1000000)'),
    ]),
    ("cert", "cert", "/acm/v1/certificates", [
        ("provision", "provision", "TLS certificate", 'domain=params.get("domain",params.get("name","unknown"))', "Would provision TLS certificate for '{domain}'", '"domain":domain,"cert_arn":f"arn:aws:acm:us-east-1:123456:certificate/{_fake_id(\"c\")}"'),
        ("delete", "delete", "TLS certificate", 'domain=params.get("domain",params.get("name","unknown"))', "Would delete TLS certificate for '{domain}'", ''),
        ("renew", "renew", "TLS certificate", 'domain=params.get("domain",params.get("name","unknown"))', "Would renew TLS certificate for '{domain}'", '"domain":domain,"new_expiry":"2027-04-12"'),
        ("status", "status", "TLS certificate", 'domain=params.get("domain",params.get("name","unknown"))', "Would fetch certificate status for '{domain}'", '"domain":domain,"status":"ISSUED","expiry":"2027-04-12","days_remaining":random.randint(30,365)'),
    ]),
    ("secret", "secret", "/secretsmanager/v1/secrets", [
        ("create", "create", "secret", 'name=params.get("name",_fake_id())', "Would create secret '{name}'", '"name":name,"secret_arn":f"arn:aws:secretsmanager:us-east-1:123456:secret:{name}"'),
        ("delete", "delete", "secret", 'name=params.get("name","unknown")', "Would delete secret '{name}'", ''),
        ("rotate", "rotate", "secret", 'name=params.get("name","unknown")', "Would rotate secret '{name}'", '"name":name,"version_id":_fake_id("v")'),
        ("get", "get", "secret", 'name=params.get("name","unknown")', "Would retrieve secret '{name}'", '"name":name,"version_stage":"AWSCURRENT"'),
        ("status", "status", "secrets", 'name=params.get("name","")', "Would list secrets status", '"total_secrets":random.randint(5,100),"rotation_enabled":random.randint(2,20)'),
    ]),
    ("kms", "key", "/kms/v1/keys", [
        ("create_key", "create_key", "KMS key", 'name=params.get("name",_fake_id())', "Would create KMS key '{name}'", '"name":name,"key_id":_fake_id("key"),"key_arn":f"arn:aws:kms:us-east-1:123456:key/{_fake_id(\"k\")}"'),
        ("delete_key", "delete_key", "KMS key", 'name=params.get("name","unknown")', "Would schedule deletion of KMS key '{name}'", '"pending_deletion_days":30'),
        ("rotate", "rotate", "KMS key", 'name=params.get("name","unknown")', "Would rotate KMS key '{name}'", '"name":name'),
        ("encrypt", "encrypt", "data", 'name=params.get("name","unknown")', "Would encrypt data with KMS key '{name}'", '"key_id":name,"ciphertext_blob":"<encrypted>"'),
        ("decrypt", "decrypt", "data", 'name=params.get("name","unknown")', "Would decrypt data with KMS key '{name}'", '"key_id":name'),
        ("status", "status", "KMS key", 'name=params.get("name","unknown")', "Would fetch status for KMS key '{name}'", '"state":"Enabled","key_rotation":"Enabled","creation_date":"2026-01-15"'),
    ]),
    ("volume", "vol", "/ebs/v1/volumes", [
        ("create", "create", "volume", 'name=params.get("name",_fake_id())\n    size=params.get("size_gb",params.get("size","100"))', "Would create {size}GB volume '{name}'", '"name":name,"volume_id":_fake_id("vol"),"size_gb":size'),
        ("delete", "delete", "volume", 'name=params.get("name","unknown")', "Would delete volume '{name}'", ''),
        ("resize", "resize", "volume", 'name=params.get("name","unknown")\n    size=params.get("size_gb","")', "Would resize volume '{name}' to {size}GB", '"name":name'),
        ("attach", "attach", "volume to instance", 'name=params.get("name","unknown")\n    instance=params.get("instance","")', "Would attach volume '{name}' to instance '{instance}'", '"name":name,"instance":instance,"device":"/dev/xvdf"'),
        ("detach", "detach", "volume from instance", 'name=params.get("name","unknown")', "Would detach volume '{name}'", '"name":name'),
        ("snapshot", "snapshot", "volume snapshot", 'name=params.get("name","unknown")', "Would create snapshot of volume '{name}'", '"name":name,"snapshot_id":_fake_id("snap")'),
        ("status", "status", "volume", 'name=params.get("name","unknown")', "Would fetch status for volume '{name}'", '"state":"in-use","size_gb":random.randint(10,2000),"iops":random.randint(100,16000)'),
    ]),
    ("filesystem", "fs", "/efs/v1/filesystems", [
        ("create", "create", "filesystem", 'name=params.get("name",_fake_id())', "Would create filesystem '{name}'", '"name":name,"fs_id":_fake_id("fs")'),
        ("delete", "delete", "filesystem", 'name=params.get("name","unknown")', "Would delete filesystem '{name}'", ''),
        ("resize", "resize", "filesystem", 'name=params.get("name","unknown")\n    size=params.get("size_gb","")', "Would resize filesystem '{name}' to {size}GB", ''),
        ("mount", "mount", "filesystem", 'name=params.get("name","unknown")\n    target=params.get("target","")', "Would mount filesystem '{name}' on '{target}'", '"mount_point":target'),
        ("status", "status", "filesystem", 'name=params.get("name","unknown")', "Would fetch status for filesystem '{name}'", '"state":"available","size_gb":round(random.uniform(1,500),1),"mount_targets":random.randint(1,5)'),
    ]),
    ("backup", "bkp", "/backup/v1", [
        ("create_plan", "create_plan", "backup plan", 'name=params.get("name",_fake_id())', "Would create backup plan '{name}'", '"name":name,"plan_id":_fake_id("bkp")'),
        ("delete_plan", "delete_plan", "backup plan", 'name=params.get("name","unknown")', "Would delete backup plan '{name}'", ''),
        ("run", "run", "backup job", 'name=params.get("name","unknown")', "Would run backup job for plan '{name}'", '"job_id":_fake_id("job"),"status":"RUNNING"'),
        ("restore", "restore", "from backup", 'name=params.get("name","unknown")\n    recovery_point=params.get("recovery_point","latest")', "Would restore from backup '{name}' recovery point '{recovery_point}'", '"restore_job_id":_fake_id("rj")'),
        ("status", "status", "backup", 'name=params.get("name","unknown")', "Would fetch backup status for '{name}'", '"last_backup":"2026-04-11T02:00:00Z","recovery_points":random.randint(1,30),"status":"COMPLETED"'),
    ]),
    ("snapshot", "snap", "/ec2/v1/snapshots", [
        ("create", "create", "snapshot", 'name=params.get("name",params.get("source","unknown"))', "Would create snapshot of '{name}'", '"snapshot_id":_fake_id("snap"),"source":name'),
        ("delete", "delete", "snapshot", 'name=params.get("name",params.get("snapshot_id","unknown"))', "Would delete snapshot '{name}'", ''),
        ("copy", "copy", "snapshot to region", 'name=params.get("name",params.get("snapshot_id","unknown"))\n    region=params.get("region","us-west-2")', "Would copy snapshot '{name}' to {region}", '"new_snapshot_id":_fake_id("snap"),"destination_region":region'),
        ("restore", "restore", "from snapshot", 'name=params.get("name",params.get("snapshot_id","unknown"))', "Would restore from snapshot '{name}'", '"resource_id":_fake_id("i")'),
        ("list", "list", "snapshots", 'env=params.get("environment","all")', "Would list snapshots for environment: {env}", '"count":random.randint(5,50)'),
    ]),
    ("autoscale", "asg", "/autoscaling/v1/groups", [
        ("create", "create", "auto-scaling group", 'name=params.get("name",_fake_id())\n    min_size=params.get("min","2")\n    max_size=params.get("max","10")', "Would create ASG '{name}' (min={min_size}, max={max_size})", '"name":name,"asg_id":_fake_id("asg"),"min":min_size,"max":max_size'),
        ("delete", "delete", "auto-scaling group", 'name=params.get("name","unknown")', "Would delete ASG '{name}'", ''),
        ("update_policy", "update_policy", "scaling policy", 'name=params.get("name","unknown")', "Would update scaling policy for ASG '{name}'", '"name":name'),
        ("status", "status", "auto-scaling group", 'name=params.get("name","unknown")', "Would fetch status for ASG '{name}'", '"desired":random.randint(2,10),"running":random.randint(2,10),"min":2,"max":10'),
    ]),
    ("apigw", "api", "/apigateway/v1", [
        ("create", "create", "API gateway", 'name=params.get("name",_fake_id())', "Would create API gateway '{name}'", '"name":name,"api_id":_fake_id("api"),"endpoint":f"https://{_fake_id(\"a\")}.execute-api.us-east-1.amazonaws.com"'),
        ("delete", "delete", "API gateway", 'name=params.get("name","unknown")', "Would delete API gateway '{name}'", ''),
        ("deploy_stage", "deploy_stage", "API to stage", 'name=params.get("name","unknown")\n    stage=params.get("stage","prod")', "Would deploy API '{name}' to stage '{stage}'", '"name":name,"stage":stage'),
        ("update_route", "update_route", "API route", 'name=params.get("name","unknown")\n    path=params.get("path","")', "Would update route '{path}' on API '{name}'", '"name":name,"path":path'),
        ("status", "status", "API gateway", 'name=params.get("name","unknown")', "Would fetch status for API '{name}'", '"stages":["dev","staging","prod"],"routes":random.randint(3,20),"requests_24h":random.randint(1000,500000)'),
    ]),
    ("servicemesh", "mesh", "/servicemesh/v1", [
        ("install", "install", "service mesh", 'name=params.get("name","istio")\n    cluster=params.get("cluster","default")', "Would install service mesh '{name}' on cluster '{cluster}'", '"name":name,"cluster":cluster'),
        ("uninstall", "uninstall", "service mesh", 'name=params.get("name","istio")', "Would uninstall service mesh '{name}'", ''),
        ("configure", "configure", "service mesh", 'name=params.get("name","istio")', "Would configure service mesh '{name}'", '"name":name'),
        ("status", "status", "service mesh", 'name=params.get("name","istio")', "Would fetch status for service mesh '{name}'", '"name":name,"state":"active","proxies":random.randint(5,50)'),
    ]),
    ("registry", "reg", "/registry/v1", [
        ("create", "create", "registry", 'name=params.get("name",_fake_id())', "Would create registry '{name}'", '"name":name,"registry_uri":f"{_fake_id(\"r\")}.dkr.ecr.us-east-1.amazonaws.com/{name}"'),
        ("delete", "delete", "registry", 'name=params.get("name","unknown")', "Would delete registry '{name}'", ''),
        ("push", "push", "artifact to registry", 'name=params.get("name","unknown")\n    artifact=params.get("artifact","")', "Would push artifact to registry '{name}'", '"name":name,"digest":f"sha256:{_fake_id(\"d\")}"'),
        ("pull", "pull", "artifact from registry", 'name=params.get("name","unknown")\n    artifact=params.get("artifact","")', "Would pull artifact from registry '{name}'", '"name":name'),
        ("status", "status", "registry", 'name=params.get("name","unknown")', "Would fetch status for registry '{name}'", '"images":random.randint(5,200),"size_gb":round(random.uniform(0.5,50),1)'),
    ]),
    ("monitor", "alarm", "/cloudwatch/v1", [
        ("create_alert", "create_alert", "alert", 'name=params.get("name",_fake_id("alarm"))\n    metric=params.get("metric","CPUUtilization")\n    threshold=params.get("threshold","80%")', "Would create alert '{name}' on {metric} > {threshold}", '"name":name,"alarm_arn":f"arn:aws:cloudwatch:us-east-1:123456:alarm:{name}"'),
        ("delete_alert", "delete_alert", "alert", 'name=params.get("name","unknown")', "Would delete alert '{name}'", ''),
        ("create_dashboard", "create_dashboard", "dashboard", 'name=params.get("name",_fake_id("dash"))', "Would create dashboard '{name}'", '"name":name,"dashboard_arn":f"arn:aws:cloudwatch::123456:dashboard/{name}"'),
        ("status", "status", "monitoring", 'name=params.get("name","")', "Would fetch monitoring status", '"alarms_ok":random.randint(5,30),"alarms_alarm":random.randint(0,3),"dashboards":random.randint(1,10)'),
    ]),
    ("log", "lg", "/logs/v1", [
        ("create_group", "create_group", "log group", 'name=params.get("name",_fake_id())', "Would create log group '{name}'", '"name":name,"log_group_arn":f"arn:aws:logs:us-east-1:123456:log-group:{name}"'),
        ("delete_group", "delete_group", "log group", 'name=params.get("name","unknown")', "Would delete log group '{name}'", ''),
        ("query", "query", "logs", 'group=params.get("group",params.get("name","unknown"))\n    query_str=params.get("query","*")', "Would query logs in '{group}'", '"results_count":random.randint(0,1000),"scanned_bytes":random.randint(10000,99999999)'),
        ("export", "export", "logs", 'group=params.get("group",params.get("name","unknown"))\n    destination=params.get("destination","s3")', "Would export logs from '{group}' to {destination}", '"export_task_id":_fake_id("task")'),
        ("status", "status", "log group", 'name=params.get("name","unknown")', "Would fetch status for log group '{name}'", '"stored_bytes":random.randint(1000000,9999999999),"retention_days":random.randint(7,365)'),
    ]),
    ("trace", "tr", "/xray/v1", [
        ("enable", "enable", "tracing", 'service=params.get("service",params.get("name","unknown"))', "Would enable tracing on service '{service}'", '"service":service'),
        ("disable", "disable", "tracing", 'service=params.get("service",params.get("name","unknown"))', "Would disable tracing on service '{service}'", ''),
        ("query", "query", "traces", 'service=params.get("service",params.get("name","unknown"))', "Would query traces for service '{service}'", '"traces_found":random.randint(10,5000),"avg_duration_ms":random.randint(10,3000)'),
        ("status", "status", "tracing", 'service=params.get("service",params.get("name","unknown"))', "Would fetch tracing status for '{service}'", '"enabled":True,"traces_24h":random.randint(1000,100000)'),
    ]),
    ("notification", "topic", "/sns/v1/topics", [
        ("create_topic", "create_topic", "topic", 'name=params.get("name",_fake_id())', "Would create notification topic '{name}'", '"name":name,"topic_arn":f"arn:aws:sns:us-east-1:123456:{name}"'),
        ("delete_topic", "delete_topic", "topic", 'name=params.get("name","unknown")', "Would delete notification topic '{name}'", ''),
        ("publish", "publish", "notification", 'name=params.get("name",params.get("topic","unknown"))', "Would publish notification to topic '{name}'", '"message_id":_fake_id("msg")'),
        ("subscribe", "subscribe", "to topic", 'name=params.get("name",params.get("topic","unknown"))\n    endpoint=params.get("endpoint","")', "Would subscribe '{endpoint}' to topic '{name}'", '"subscription_arn":f"arn:aws:sns:us-east-1:123456:{name}:{_fake_id(\"s\")}"'),
        ("status", "status", "notification topic", 'name=params.get("name","unknown")', "Would fetch status for topic '{name}'", '"subscriptions":random.randint(1,20),"messages_published_24h":random.randint(0,10000)'),
    ]),
    ("email", "ses", "/ses/v1", [
        ("configure", "configure", "email service", 'domain=params.get("domain",params.get("name","unknown"))', "Would configure email service for '{domain}'", '"domain":domain'),
        ("send", "send", "email", 'to=params.get("to","unknown")\n    sender=params.get("from",params.get("sender","noreply@example.com"))', "Would send email from '{sender}' to '{to}'", '"message_id":_fake_id("msg")'),
        ("verify_domain", "verify_domain", "domain", 'domain=params.get("domain",params.get("name","unknown"))', "Would verify domain '{domain}' for email sending", '"domain":domain,"verification_token":_fake_id("tok")'),
        ("status", "status", "email service", 'domain=params.get("domain",params.get("name",""))', "Would fetch email service status", '"send_quota_24h":50000,"sent_24h":random.randint(100,10000),"bounce_rate":f"{round(random.uniform(0,5),1)}%"'),
    ]),
    ("workflow", "wf", "/stepfunctions/v1", [
        ("create", "create", "workflow", 'name=params.get("name",_fake_id())', "Would create workflow '{name}'", '"name":name,"workflow_arn":f"arn:aws:states:us-east-1:123456:stateMachine:{name}"'),
        ("delete", "delete", "workflow", 'name=params.get("name","unknown")', "Would delete workflow '{name}'", ''),
        ("execute", "execute", "workflow", 'name=params.get("name","unknown")', "Would execute workflow '{name}'", '"execution_id":_fake_id("exec"),"status":"RUNNING"'),
        ("status", "status", "workflow", 'name=params.get("name","unknown")', "Would fetch status for workflow '{name}'", '"state":"ACTIVE","executions_24h":random.randint(0,100),"last_status":"SUCCEEDED"'),
    ]),
    ("scheduler", "sched", "/scheduler/v1/schedules", [
        ("create", "create", "schedule", 'name=params.get("name",_fake_id())\n    schedule=params.get("schedule",params.get("cron","rate(1 hour)"))', "Would create schedule '{name}' ({schedule})", '"name":name,"schedule_arn":f"arn:aws:scheduler:us-east-1:123456:schedule/{name}"'),
        ("delete", "delete", "schedule", 'name=params.get("name","unknown")', "Would delete schedule '{name}'", ''),
        ("enable", "enable", "schedule", 'name=params.get("name","unknown")', "Would enable schedule '{name}'", '"name":name,"state":"ENABLED"'),
        ("disable", "disable", "schedule", 'name=params.get("name","unknown")', "Would disable schedule '{name}'", '"name":name,"state":"DISABLED"'),
        ("status", "status", "schedule", 'name=params.get("name","unknown")', "Would fetch status for schedule '{name}'", '"state":"ENABLED","next_run":"2026-04-13T02:00:00Z","last_run":"2026-04-12T02:00:00Z"'),
    ]),
    ("batch", "job", "/batch/v1/jobs", [
        ("create_job", "create_job", "batch job", 'name=params.get("name",_fake_id())', "Would create batch job definition '{name}'", '"name":name,"job_def_arn":f"arn:aws:batch:us-east-1:123456:job-definition/{name}"'),
        ("delete_job", "delete_job", "batch job", 'name=params.get("name","unknown")', "Would delete batch job definition '{name}'", ''),
        ("submit", "submit", "batch job", 'name=params.get("name","unknown")', "Would submit batch job '{name}'", '"job_id":_fake_id("job"),"status":"SUBMITTED"'),
        ("status", "status", "batch job", 'name=params.get("name","unknown")', "Would fetch status for batch job '{name}'", '"status":"SUCCEEDED","duration_s":random.randint(30,3600)'),
    ]),
    ("etl", "pipe", "/glue/v1/pipelines", [
        ("create_pipeline", "create_pipeline", "ETL pipeline", 'name=params.get("name",_fake_id())', "Would create ETL pipeline '{name}'", '"name":name,"pipeline_id":_fake_id("pipe")'),
        ("delete_pipeline", "delete_pipeline", "ETL pipeline", 'name=params.get("name","unknown")', "Would delete ETL pipeline '{name}'", ''),
        ("run", "run", "ETL pipeline", 'name=params.get("name","unknown")', "Would run ETL pipeline '{name}'", '"run_id":_fake_id("run"),"status":"RUNNING"'),
        ("status", "status", "ETL pipeline", 'name=params.get("name","unknown")', "Would fetch status for ETL pipeline '{name}'", '"state":"READY","last_run_status":"SUCCEEDED","last_run_duration_s":random.randint(60,7200)'),
    ]),
    ("warehouse", "wh", "/redshift/v1/clusters", [
        ("provision", "provision", "data warehouse", 'name=params.get("name",_fake_id())\n    nodes=params.get("nodes","2")\n    node_type=params.get("node_type","dc2.large")', "Would provision warehouse '{name}' ({nodes}x {node_type})", '"name":name,"cluster_id":_fake_id("wh"),"endpoint":f"{name}.{_fake_id(\"c\")}.us-east-1.redshift.amazonaws.com:5439"'),
        ("delete", "delete", "data warehouse", 'name=params.get("name","unknown")', "Would delete data warehouse '{name}'", ''),
        ("resize", "resize", "data warehouse", 'name=params.get("name","unknown")\n    nodes=params.get("nodes","")', "Would resize warehouse '{name}' to {nodes} nodes", ''),
        ("query", "query", "data warehouse", 'name=params.get("name","unknown")', "Would execute query against warehouse '{name}'", '"query_id":_fake_id("q"),"rows_returned":random.randint(0,100000),"duration_ms":random.randint(100,30000)'),
        ("status", "status", "data warehouse", 'name=params.get("name","unknown")', "Would fetch status for warehouse '{name}'", '"state":"available","nodes":random.randint(1,8),"cpu_usage":f"{random.randint(5,80)}%","storage_used":f"{random.randint(10,90)}%"'),
    ]),
    ("datalake", "lake", "/lakeformation/v1", [
        ("create", "create", "data lake", 'name=params.get("name",_fake_id())', "Would create data lake '{name}'", '"name":name,"lake_id":_fake_id("lake")'),
        ("delete", "delete", "data lake", 'name=params.get("name","unknown")', "Would delete data lake '{name}'", ''),
        ("set_permissions", "set_permissions", "data lake permissions", 'name=params.get("name","unknown")', "Would set permissions on data lake '{name}'", '"name":name'),
        ("status", "status", "data lake", 'name=params.get("name","unknown")', "Would fetch status for data lake '{name}'", '"state":"active","tables":random.randint(5,200),"size_tb":round(random.uniform(0.1,50),1)'),
    ]),
    ("search", "es", "/opensearch/v1/domains", [
        ("create", "create", "search cluster", 'name=params.get("name",_fake_id())\n    nodes=params.get("nodes","3")', "Would create search cluster '{name}' ({nodes} nodes)", '"name":name,"domain_id":_fake_id("es"),"endpoint":f"search-{name}-{_fake_id(\"x\")}.us-east-1.es.amazonaws.com"'),
        ("delete", "delete", "search cluster", 'name=params.get("name","unknown")', "Would delete search cluster '{name}'", ''),
        ("resize", "resize", "search cluster", 'name=params.get("name","unknown")\n    nodes=params.get("nodes","")', "Would resize search cluster '{name}' to {nodes} nodes", ''),
        ("reindex", "reindex", "search index", 'name=params.get("name","unknown")', "Would reindex search cluster '{name}'", '"task_id":_fake_id("task")'),
        ("status", "status", "search cluster", 'name=params.get("name","unknown")', "Would fetch status for search cluster '{name}'", '"state":"active","indices":random.randint(5,100),"docs":random.randint(10000,10000000),"storage_gb":round(random.uniform(1,500),1)'),
    ]),
    ("ml", "ml", "/sagemaker/v1/endpoints", [
        ("create_endpoint", "create_endpoint", "ML endpoint", 'name=params.get("name",_fake_id())\n    instance_type=params.get("instance_type","ml.m5.xlarge")', "Would create ML endpoint '{name}' ({instance_type})", '"name":name,"endpoint_arn":f"arn:aws:sagemaker:us-east-1:123456:endpoint/{name}"'),
        ("delete_endpoint", "delete_endpoint", "ML endpoint", 'name=params.get("name","unknown")', "Would delete ML endpoint '{name}'", ''),
        ("deploy_model", "deploy_model", "model to endpoint", 'name=params.get("name","unknown")\n    model=params.get("model","")', "Would deploy model '{model}' to endpoint '{name}'", '"name":name,"model":model'),
        ("status", "status", "ML endpoint", 'name=params.get("name","unknown")', "Would fetch status for ML endpoint '{name}'", '"state":"InService","invocations_5m":random.randint(10,5000),"latency_p99_ms":random.randint(10,500)'),
    ]),
    ("notebook", "nb", "/sagemaker/v1/notebooks", [
        ("create", "create", "notebook", 'name=params.get("name",_fake_id())\n    instance_type=params.get("instance_type","ml.t3.medium")', "Would create notebook '{name}' ({instance_type})", '"name":name,"notebook_arn":f"arn:aws:sagemaker:us-east-1:123456:notebook-instance/{name}"'),
        ("delete", "delete", "notebook", 'name=params.get("name","unknown")', "Would delete notebook '{name}'", ''),
        ("start", "start", "notebook", 'name=params.get("name","unknown")', "Would start notebook '{name}'", '"name":name,"state":"InService"'),
        ("stop", "stop", "notebook", 'name=params.get("name","unknown")', "Would stop notebook '{name}'", '"name":name,"state":"Stopped"'),
        ("status", "status", "notebook", 'name=params.get("name","unknown")', "Would fetch status for notebook '{name}'", '"state":"InService","instance_type":params.get("instance_type","ml.t3.medium"),"uptime_hrs":random.randint(1,168)'),
    ]),
    ("iot", "iot", "/iot/v1", [
        ("create_thing", "create_thing", "IoT thing", 'name=params.get("name",_fake_id())', "Would register IoT thing '{name}'", '"name":name,"thing_arn":f"arn:aws:iot:us-east-1:123456:thing/{name}"'),
        ("delete_thing", "delete_thing", "IoT thing", 'name=params.get("name","unknown")', "Would delete IoT thing '{name}'", ''),
        ("create_rule", "create_rule", "IoT rule", 'name=params.get("name",_fake_id("rule"))', "Would create IoT rule '{name}'", '"name":name,"rule_arn":f"arn:aws:iot:us-east-1:123456:rule/{name}"'),
        ("status", "status", "IoT", 'name=params.get("name","")', "Would fetch IoT status", '"things":random.randint(1,1000),"rules":random.randint(1,50),"connected":random.randint(1,500)'),
    ]),
    ("transfer", "dms", "/dms/v1/tasks", [
        ("create_job", "create_job", "transfer job", 'name=params.get("name",_fake_id())\n    source=params.get("source","")\n    target=params.get("target","")', "Would create transfer job '{name}' ({source} → {target})", '"name":name,"task_arn":f"arn:aws:dms:us-east-1:123456:task:{_fake_id(\"t\")}"'),
        ("delete_job", "delete_job", "transfer job", 'name=params.get("name","unknown")', "Would delete transfer job '{name}'", ''),
        ("start", "start", "transfer job", 'name=params.get("name","unknown")', "Would start transfer job '{name}'", '"name":name,"status":"running"'),
        ("status", "status", "transfer job", 'name=params.get("name","unknown")', "Would fetch status for transfer job '{name}'", '"status":"running","tables_loaded":random.randint(1,100),"rows_transferred":random.randint(1000,10000000),"replication_lag_s":round(random.uniform(0,10),1)'),
    ]),
    ("config", "cfg", "/config/v1/rules", [
        ("create_rule", "create_rule", "config rule", 'name=params.get("name",_fake_id())', "Would create config rule '{name}'", '"name":name,"rule_arn":f"arn:aws:config:us-east-1:123456:config-rule/{name}"'),
        ("delete_rule", "delete_rule", "config rule", 'name=params.get("name","unknown")', "Would delete config rule '{name}'", ''),
        ("evaluate", "evaluate", "compliance", 'name=params.get("name","unknown")', "Would evaluate compliance for rule '{name}'", '"compliant":random.randint(50,200),"non_compliant":random.randint(0,20)'),
        ("status", "status", "config rules", 'name=params.get("name","")', "Would fetch config compliance status", '"rules":random.randint(5,50),"compliant_resources":random.randint(50,500),"non_compliant":random.randint(0,30)'),
    ]),
    ("compliance", "comp", "/securityhub/v1", [
        ("run_scan", "run_scan", "compliance scan", 'scope=params.get("scope",params.get("name","all"))', "Would run compliance scan on '{scope}'", '"scan_id":_fake_id("scan"),"status":"RUNNING"'),
        ("create_policy", "create_policy", "compliance policy", 'name=params.get("name",_fake_id())', "Would create compliance policy '{name}'", '"name":name,"policy_arn":f"arn:aws:securityhub:us-east-1:123456:policy/{name}"'),
        ("status", "status", "compliance", 'name=params.get("name","")', "Would fetch compliance status", '"score":random.randint(60,100),"critical":random.randint(0,5),"high":random.randint(0,20),"passed":random.randint(50,200)'),
    ]),
    ("image", "ami", "/ec2/v1/images", [
        ("create", "create", "machine image", 'name=params.get("name",_fake_id())\n    source=params.get("source","")', "Would create machine image '{name}' from '{source}'", '"name":name,"image_id":_fake_id("ami")'),
        ("delete", "delete", "machine image", 'name=params.get("name","unknown")', "Would delete machine image '{name}'", ''),
        ("share", "share", "machine image", 'name=params.get("name","unknown")\n    account=params.get("account","")', "Would share image '{name}' with account '{account}'", '"name":name,"account":account'),
        ("deregister", "deregister", "machine image", 'name=params.get("name","unknown")', "Would deregister machine image '{name}'", ''),
        ("list", "list", "machine images", 'env=params.get("environment","all")', "Would list machine images for environment: {env}", '"count":random.randint(5,100)'),
    ]),
    ("dr", "dr", "/drs/v1", [
        ("create_plan", "create_plan", "DR plan", 'name=params.get("name",_fake_id())', "Would create DR plan '{name}'", '"name":name,"plan_id":_fake_id("dr")'),
        ("failover", "failover", "DR failover", 'name=params.get("name","unknown")\n    region=params.get("region","us-west-2")', "Would initiate failover for '{name}' to {region}", '"name":name,"failover_id":_fake_id("fo"),"target_region":region'),
        ("failback", "failback", "DR failback", 'name=params.get("name","unknown")', "Would initiate failback for '{name}' to primary", '"name":name,"failback_id":_fake_id("fb")'),
        ("test", "test", "DR drill", 'name=params.get("name","unknown")', "Would run DR test drill for '{name}'", '"test_id":_fake_id("test"),"status":"RUNNING"'),
        ("status", "status", "DR plan", 'name=params.get("name","unknown")', "Would fetch DR status for '{name}'", '"state":"ready","rpo_minutes":random.randint(1,60),"rto_minutes":random.randint(5,120),"last_test":"2026-04-01"'),
    ]),
]


def generate_handler(domain, prefix, api_base, actions):
    lines = []
    lines.append("import random")
    lines.append("import string")
    lines.append("from datetime import datetime")
    lines.append("")
    lines.append("")
    lines.append(f'def _fake_id(prefix="{prefix}"):')
    lines.append('    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))')
    lines.append('    return f"{prefix}-{suffix}"')
    lines.append("")
    lines.append("")
    lines.append("def handle(intent, params, dry_run):")
    lines.append("    handler = {")
    for action_name, suffix, _, _, _, _ in actions:
        lines.append(f'        "{domain}.{suffix}": _{action_name},')
    lines.append("    }.get(intent)")
    lines.append("    if not handler:")
    lines.append(f'        return {{"status": "error", "message": f"No {domain} handler for intent: {{intent}}"}}')
    lines.append("    return handler(params, dry_run)")
    lines.append("")

    for action_name, suffix, desc, param_code, dry_msg, sim_extras in actions:
        lines.append("")
        lines.append(f"def _{action_name}(params, dry_run):")
        for p in param_code.split("\n"):
            lines.append(f"    {p.strip()}")
        lines.append("    if dry_run:")

        # Determine the HTTP method from action name
        if action_name in ("create", "provision", "create_role", "create_user", "create_key",
                           "create_plan", "create_pipeline", "create_job", "create_thing",
                           "create_rule", "create_topic", "create_alert", "create_dashboard",
                           "create_group", "create_endpoint", "create_policy",
                           "deploy", "push", "run_scan", "submit", "run", "execute",
                           "attach", "mount", "enable", "invoke", "publish", "subscribe",
                           "send", "configure", "verify_domain", "install", "deploy_stage",
                           "deploy_model", "start", "failover", "failback", "test",
                           "attach_policy", "snapshot", "copy", "update_route", "push"):
            method = "POST"
        elif action_name in ("delete", "delete_role", "delete_key", "delete_plan",
                             "delete_pipeline", "delete_job", "delete_thing",
                             "delete_rule", "delete_topic", "delete_alert",
                             "delete_group", "delete_endpoint", "delete_policy",
                             "uninstall", "detach", "disable", "deregister",
                             "flush", "purge"):
            method = "DELETE"
        elif action_name in ("resize", "update_policy", "update_rules", "update_config",
                             "set_permissions", "rotate", "renew", "reindex",
                             "invalidate", "evaluate", "lifecycle"):
            method = "PUT"
        elif action_name in ("status", "list", "get", "query", "pull", "export",
                             "decrypt"):
            method = "GET"
        else:
            method = "POST"

        api_path = f"{method} {api_base}"
        lines.append(f'        return {{"status": "dry_run", "message": f"{dry_msg}", "would_call": "{api_path}"}}')

        # Simulate response
        if sim_extras:
            lines.append(f'    return {{"status": "success", "message": f"{desc} completed", {sim_extras}, "at": datetime.utcnow().isoformat() + "Z"}}')
        else:
            lines.append(f'    return {{"status": "success", "message": f"{desc} completed", "at": datetime.utcnow().isoformat() + "Z"}}')

    return "\n".join(lines) + "\n"


def main():
    created = 0
    for domain, prefix, api_base, actions in DOMAINS:
        filename = f"{domain}_handler.py"
        filepath = os.path.join(HANDLERS_DIR, filename)
        if os.path.exists(filepath):
            print(f"  SKIP  {filename} (already exists)")
            continue
        content = generate_handler(domain, prefix, api_base, actions)
        with open(filepath, "w") as f:
            f.write(content)
        created += 1
        print(f"  OK    {filename}")
    print(f"\n  Created {created} handler files")


if __name__ == "__main__":
    main()
