/* RSOS v1.3 Python worker. Original archived source is verified by Git blob SHA-1 before execution. */
"use strict";
const INDEX_URL="https://cdn.jsdelivr.net/pyodide/v0.27.7/full/";
const SOURCE_BLOB_SHA1="eb05bc81bf448bc1b47226b65aee251c313c958b";
let pyodide=null,initialized=false,initializing=null,running=false;
const status=message=>self.postMessage({type:"status",message});
const errorToString=e=>e&&e.message?e.message:String(e);
async function sha1GitBlob(source){
  const body=new TextEncoder().encode(source),header=new TextEncoder().encode("blob "+body.length+"\0");
  const bytes=new Uint8Array(header.length+body.length);bytes.set(header);bytes.set(body,header.length);
  const digest=await crypto.subtle.digest("SHA-1",bytes);
  return [...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,"0")).join("");
}
async function init(){
  if(initialized)return;
  if(initializing)return initializing;
  initializing=(async()=>{
    status("Downloading pinned Python runtime (first visit needs network access)...");
    importScripts(INDEX_URL+"pyodide.js");
    pyodide=await loadPyodide({indexURL:INDEX_URL});
    status("Loading NumPy and pandas...");
    await pyodide.loadPackage(["numpy","pandas"]);
    status("Verifying the original v1.3 Python research source...");
    const response=await fetch(new URL("./transfer_benchmark.py",self.location.href),{cache:"no-store"});
    if(!response.ok)throw Error("Archived source unavailable: HTTP "+response.status);
    const source=await response.text();
    const blob=await sha1GitBlob(source);
    if(blob!==SOURCE_BLOB_SHA1)throw Error("Pinned source integrity mismatch. Expected "+SOURCE_BLOB_SHA1+"; received "+blob);
    pyodide.FS.writeFile("/tmp/rsos_v13_pinned.py",source);
    await pyodide.runPythonAsync(
      "import importlib.util\n"+
      "_spec=importlib.util.spec_from_file_location('rsos_v13_pinned','/tmp/rsos_v13_pinned.py')\n"+
      "v13=importlib.util.module_from_spec(_spec)\n"+
      "_spec.loader.exec_module(v13)"
    );
    initialized=true;status("Verified v1.3 Python source loaded.");
  })();
  try{await initializing}catch(e){initialized=false;initializing=null;throw e}
}
const executePython="\nimport json\np=json.loads(params_json)\nd=v13.run(seed=p[\"seed\"],people=p[\"people\"],calibration=24,tests=p[\"tests\"],design=p[\"design\"],threshold=p[\"threshold\"],hard_ood=p[\"hard_ood\"])\nmeans={str(k):float(v) for k,v in d.groupby(\"model\")[\"regret\"].mean().items()}\nworlds={}\nfor (w,m),v in d.groupby([\"world\",\"model\"])[\"regret\"].mean().items():\n    worlds.setdefault(str(w),{})[str(m)]=float(v)\na=d[d.model==\"rsia_evidence_gate\"].sort_values([\"world\",\"person\",\"trial\"])\nb=d[d.model==\"generic_same_gate\"].sort_values([\"world\",\"person\",\"trial\"])\nsame_regret=bool((a[\"regret\"].to_numpy()==b[\"regret\"].to_numpy()).all())\nsame_selection=bool((a[\"selected_program\"].to_numpy()==b[\"selected_program\"].to_numpy()).all())\ngate=a[[\"world\",\"person\",\"eta\",\"uses_relation\"]].drop_duplicates([\"world\",\"person\"])\ncases=[]\nfor world_name in v13.WORLDS:\n    x=a[a.world==world_name].iloc[0]\n    rows=d[(d.world==world_name)&(d.person==int(x.person))&(d.trial==int(x.trial))]\n    cases.append({\n       \"world\":world_name,\"context\":int(x.context),\"person\":int(x.person),\n       \"trial\":int(x.trial),\"eta\":float(x.eta),\"gate_uses_relation\":bool(x.uses_relation),\n       \"arms\":{str(r[\"model\"]):{\"program\":int(r[\"selected_program\"]),\n             \"glyph\":int(v13.ARMS[int(r[\"selected_program\"]),0]),\n             \"sound\":int(v13.ARMS[int(r[\"selected_program\"]),1]),\n             \"operator\":int(v13.ARMS[int(r[\"selected_program\"]),2]),\n             \"regret\":float(r[\"regret\"])}\n             for _,r in rows.iterrows()}\n    })\nout={\n    \"kind\":\"rsos_v13_original_python_live\",\n    \"source_git_blob_sha1\":\"eb05bc81bf448bc1b47226b65aee251c313c958b\",\n    \"archived_tag\":\"v1.0.0-research-preview\",\n    \"seed\":p[\"seed\"],\"people_per_world\":p[\"people\"],\"calibration\":24,\n    \"tests_per_person\":p[\"tests\"],\"design\":p[\"design\"],\"threshold\":p[\"threshold\"],\n    \"hard_ood\":p[\"hard_ood\"],\"worlds\":list(v13.WORLDS),\"models\":list(v13.MODELS),\n    \"decisions_per_policy\":int(len(a)),\"total_policy_rows\":int(len(d)),\n    \"mean_regret\":means,\"world_mean_regret\":worlds,\n    \"same_gate_exact_regret_tie\":same_regret,\n    \"same_gate_exact_selection_tie\":same_selection,\n    \"relation_usage_rate\":float(gate[\"uses_relation\"].mean()),\n    \"cases\":cases,\n    \"limitations\":\"Synthetic Python v1.3, subset of people/seeds; no human or neural outcomes. Full reported holdout uses three seeds, 48 people per world and 16 trials.\"\n}\nresult_json=json.dumps(out,allow_nan=False,separators=(\",\",\":\"))\n";
function validate(v){
  if(!v||typeof v!=="object")throw Error("Missing configuration");
  const seed=Number(v.seed),people=Number(v.people),tests=Number(v.tests),threshold=Number(v.threshold);
  if(![63011,63012,63013,64011,64012,64013].includes(seed))throw Error("Unrecognized research seed");
  if(!Number.isInteger(people)||people<1||people>12)throw Error("People must be 1–12");
  if(![2,4,8,16].includes(tests))throw Error("Trials must be 2, 4, 8, or 16");
  if(!Number.isFinite(threshold)||threshold<0||threshold>1)throw Error("Threshold must be in [0,1]");
  if(!["random","balanced"].includes(v.design))throw Error("Unknown calibration design");
  return {seed,people,tests,threshold,design:v.design,hard_ood:!!v.hard_ood};
}
self.addEventListener("message",async event=>{
  if(event.data?.type!=="run")return;
  if(running){status("A benchmark is already running.");return}
  running=true;
  try{
    const params=validate(event.data.params);
    await init();
    status("Executing original v1.3 Python across eight synthetic environments and 11 policies...");
    pyodide.globals.set("params_json",JSON.stringify(params));
    const data=JSON.parse(await pyodide.runPythonAsync(executePython+"\nresult_json"));
    if(!data.same_gate_exact_regret_tie||!data.same_gate_exact_selection_tie)
      throw Error("Required equal-model negative control failed: results withheld.");
    self.postMessage({type:"result",result:data});
  }catch(e){self.postMessage({type:"error",message:errorToString(e)})}
  finally{running=false}
});
