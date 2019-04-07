#!/bin/ksh
#
# QueueName: KourouOnline
# TargetName: TestCaseOnlineStress.install
# ProjectRef: xse06/InstallersDoyle/Kourou/11063
# ReleaseLogs: u:\pgxbe\logs\20180620-214541-5335-xse06-Product-XeikonSoftware
# ScriptFile: u:\pgxbe\releases\xse06\InstallersDoyle\Kourou\11063\Doyle;Q=KourouOnline;T=TestCaseOnlineStress.install;N.sh

function ReportSkipped
{
    echo "The test is skipped. $1"
    echo "'Mail successfully sent' is echoed to block mail."
}

export XBERELEASELOGPATH="u:\\pgxbe\\logs\\20180620-214541-5335-xse06-Product-XeikonSoftware"
export XBEHOME="u:\\pgxbe\\releases\\xse06\\InstallersDoyle\\Kourou\\11063"
export XBEDOYLESCRIPT="Doyle;Q=KourouOnline;T=TestCaseOnlineStress.install;N.sh"
export tfsbuildflavor="Release"
export tfsbuildid="33440"
export tfsbuildname="xse06_Product_XeikonSoftware"
export tfsbuildplatform="Any CPU"
export tfsbuildproject="http://tfs:8080/tfs/defaultcollection"
export tfsbuildprojectname="PGX"

. "${XBEHOME//\\//}/${XBEDOYLESCRIPT}" $1
