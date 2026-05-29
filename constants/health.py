from models.health import HealthCondition

# Polish labels for observed health conditions (section "Zdrowie").
HEALTH_LABELS: dict[str, str] = {
    HealthCondition.dwv: "Wirus zdeformowanych skrzydeł (DWV)",
    HealthCondition.foulbrood: "Zgnilec",
    HealthCondition.dysentery: "Biegunka / nosemoza",
    HealthCondition.varroa: "Warroza (Varroa destructor)",
    HealthCondition.chalkbrood: "Grzybica wapienna (kreteń)",
    HealthCondition.acarine: "Choroba roztoczowa (akarioza)",
    HealthCondition.wax_moth: "Barciak (mól woskowy)",
    HealthCondition.other: "Inne",
}
