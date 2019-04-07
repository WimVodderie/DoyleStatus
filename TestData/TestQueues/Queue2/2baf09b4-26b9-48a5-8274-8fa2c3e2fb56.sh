#!/bin/ksh
#
# QueueName: KourouOnline
# TargetName: TestCaseMetaDataPrint.install
# ProjectRef: xse06/InstallersDoyle/Kourou/11065
# ReleaseLogs: u:\pgxbe\logs\20180621-110116-3376-xse06-InstallersDoyle-KourouPlus
# ScriptFile: u:\pgxbe\releases\xse06\InstallersDoyle\Kourou\11065\Doyle;Q=KourouOnline;T=TestCaseMetaDataPrint.install;A.sh

function ReportSkipped
{
    echo "The test is skipped. $1"
    echo "'Mail successfully sent' is echoed to block mail."
}

export XBERELEASELOGPATH="u:\\pgxbe\\logs\\20180621-110116-3376-xse06-InstallersDoyle-KourouPlus"
export XBEHOME="u:\\pgxbe\\releases\\xse06\\InstallersDoyle\\Kourou\\11065"
export XBEDOYLESCRIPT="Doyle;Q=KourouOnline;T=TestCaseMetaDataPrint.install;A.sh"
export tfsbuildflavor="Release"
export tfsbuildid="33446"
export tfsbuildname="xse06_InstallersDoyle_KourouPlus"
export tfsbuildplatform="Any CPU"
export tfsbuildproject="http://tfs:8080/tfs/defaultcollection"
export tfsbuildprojectname="PGX"

if [ "$(xbe_getlr -t xse06 InstallersDoyle Kourou)" != "11065" ]
then
    ReportSkipped "There is a later release."; exit 0
fi

if [ "$(/usr/bin/find "${XBEHOME//\\//}" -maxdepth 1 -name "${XBEDOYLESCRIPT}.lock" -mmin -720 -printf 1)" == "1" ]
then
    ReportSkipped "It was already executed recently."; exit 0
fi

. "${XBEHOME//\\//}/${XBEDOYLESCRIPT}" $1
