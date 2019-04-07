#!/bin/ksh
#
# QueueName: OnlineDuplexMiral
# TargetName: TestCaseLogPackage.install
# ProjectRef: xse0600/InstallersDoyle/Kourou/10936
# ReleaseLogs: u:\pgxbe\logs\20180621-150016-6064-xse0600-InstallersDoyle-Kourou
# ScriptFile: u:\pgxbe\releases\xse0600\InstallersDoyle\Kourou\10936\Doyle;Q=OnlineDuplexMiral;T=TestCaseLogPackage.install;A.sh

function ReportSkipped
{
    echo "The test is skipped. $1"
    echo "'Mail successfully sent' is echoed to block mail."
}

export XBERELEASELOGPATH="u:\\pgxbe\\logs\\20180621-150016-6064-xse0600-InstallersDoyle-Kourou"
export XBEHOME="u:\\pgxbe\\releases\\xse0600\\InstallersDoyle\\Kourou\\10936"
export XBEDOYLESCRIPT="Doyle;Q=OnlineDuplexMiral;T=TestCaseLogPackage.install;A.sh"
export tfsbuildflavor="Release"
export tfsbuildid="33453"
export tfsbuildname="xse0600_InstallersDoyle_Kourou"
export tfsbuildplatform="Any CPU"
export tfsbuildproject="http://tfs:8080/tfs/defaultcollection"
export tfsbuildprojectname="PGX"

if [ "$(xbe_getlr -t xse0600 InstallersDoyle Kourou)" != "10936" ]
then
    ReportSkipped "There is a later release."; exit 0
fi

if [ "$(/usr/bin/find "${XBEHOME//\\//}" -maxdepth 1 -name "${XBEDOYLESCRIPT}.lock" -mmin -720 -printf 1)" == "1" ]
then
    ReportSkipped "It was already executed recently."; exit 0
fi

. "${XBEHOME//\\//}/${XBEDOYLESCRIPT}" $1