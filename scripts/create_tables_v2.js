// Uses Catalyst CLI's internal SDK to create tables
const path = require("path");

// Load the CLI's internal SDK
const sdkPath = path.join(process.env.APPDATA, "npm", "node_modules", "zcatalyst-cli", "node_modules", "zcatalyst-sdk-node");
const Catalyst = require(sdkPath).CatalystApp || require(sdkPath);

async function main() {
  const app = Catalyst.initialize({ type: "byok", projectId: "55029000000013055" });
  const ds = app.datastore();
  const tables = [
    "CasteMaster","ReligionMaster","OccupationMaster","CaseCategory",
    "GravityOffence","CaseStatusMaster","UnitType","Rank","Designation",
    "State","District","Court","Unit","Employee",
    "Act","Section","CrimeHead","CrimeSubHead","CrimeHeadActSection",
    "CaseMaster","ComplainantDetails","ActSectionAssociation",
    "Victim","Accused","ArrestSurrender","ChargesheetDetails",
    "Inv_OccuranceTime","inv_arrestsurrenderaccused",
    "CrimePattern","Alert","Prediction","ChatContext","BehaviorProfile","TimelineEvent"
  ];
  for (const t of tables) {
    try {
      await ds.createTable(t);
      console.log("OK:", t);
    } catch (e) {
      console.log("ERR:", t, "-", e.message?.slice(0,60));
    }
  }
}
main().catch(console.error);
