const { CatalystApp } = require("zcatalyst-sdk-node");
const path = require("path");

async function createTables() {
  try {
    const app = CatalystApp.initialize({ projectId: "55029000000013055", projectKey: "development" }, { type: "byok" });
    const datastore = app.datastore();
    const tables = [
      "CasteMaster", "ReligionMaster", "OccupationMaster", "CaseCategory",
      "GravityOffence", "CaseStatusMaster", "UnitType", "Rank", "Designation",
      "State", "District", "Court", "Unit", "Employee",
      "Act", "Section", "CrimeHead", "CrimeSubHead", "CrimeHeadActSection",
      "CaseMaster", "ComplainantDetails", "ActSectionAssociation",
      "Victim", "Accused", "ArrestSurrender", "ChargesheetDetails",
      "Inv_OccuranceTime", "inv_arrestsurrenderaccused",
      "CrimePattern", "Alert", "Prediction", "ChatContext",
      "BehaviorProfile", "TimelineEvent"
    ];
    for (const name of tables) {
      try {
        await datastore.createTable(name);
        console.log(`Created: ${name}`);
      } catch (e) {
        console.log(`Skip ${name}: ${e.message}`);
      }
    }
    console.log("Done");
  } catch (e) {
    console.error("Error:", e.message);
  }
}
createTables();
