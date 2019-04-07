#!/bin/ksh
#
# QueueName: KourouOnline
# TargetName: TestCaseMetaDataPrint.install
# ProjectRef: xse060x/InstallersDoyle/Kourou/10878
# ReleaseLogs: u:\pgxbe\logs\20180621-134301-9812-xse060x-InstallersDoyle-Kourou
# ScriptFile: u:\pgxbe\releases\xse060x\InstallersDoyle\Kourou\10878\Doyle;Q=KourouOnline;T=TestCaseMetaDataPrint.install;A.sh

function ReportSkipped
{
    echo "The test is skipped. $1"
    echo "'Mail successfully sent' is echoed to block mail."
}

export XBERELEASELOGPATH="u:\\pgxbe\\logs\\20180621-134301-9812-xse060x-InstallersDoyle-Kourou"
export XBEHOME="u:\\pgxbe\\releases\\xse060x\\InstallersDoyle\\Kourou\\10878"
export XBEDOYLESCRIPT="Doyle;Q=KourouOnline;T=TestCaseMetaDataPrint.install;A.sh"
export tfsbuildflavor="Release"
export tfsbuildid="33451"
export tfsbuildname="xse060x_InstallersDoyle_Kourou"
export tfsbuildplatform="Any CPU"
export tfsbuildproject="http://tfs:8080/tfs/defaultcollection"
export tfsbuildprojectname="PGX"

if [ "$(xbe_getlr -t xse060x InstallersDoyle Kourou)" != "10878" ]
then
    ReportSkipped "There is a later release."; exit 0
fi

if [ "$(/usr/bin/find "${XBEHOME//\\//}" -maxdepth 1 -name "${XBEDOYLESCRIPT}.lock" -mmin -720 -printf 1)" == "1" ]
then
    ReportSkipped "It was already executed recently."; exit 0
fi

. "${XBEHOME//\\//}/${XBEDOYLESCRIPT}" $1
