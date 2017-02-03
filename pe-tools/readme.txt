# misc hacks for querying puppet database

examples:
# show all changes from the last run in melbourne
pe-get-changes  | jq '.[] | select(.environment == "melbourne")'
# same as above but filter out any swift classes (also limit/tidy up output to specific fields)
pe-get-changes  | jq '.[] | select(.environment == "melbourne" and (select(."containing-class" | contains("Swift") | not))) | { class: ."containing-class", res: ."resource-title", host: .certname, msg: .message, end: ."run-end-time", status: .status, path: ."containment-path"}' | less

# show all failures from last runs in any spartan host
pe-get-failures | jq '.[] | select(.certname | contains("spartan"))'
# and filter/tidy up output
pe-get-failures | jq '.[] | select(.certname | contains("spartan")) | {class: ."containing-class", type: ."resource-title", msg: .message, end: ."run-end-time" }'             

# get all facts for a host
pe-get-host-facts <hostname>
# get facts for sda
pe-get-host-facts <hostname> | jq '.[] | select( .name | contains("blockdevice_sda"))'
# get model of all hd's
pe-get-host-facts <hostname> | jq '.[] | select( .name | test("blockdevice_.*_model"))'
# add  '| { model: .value, device: .name}' to tidy

# get asset tags/serial numbers for all melbourne hosts
pe-get-hosts boardserialnumber | jq '.[] | select( .environment == "melbourne" ) | {host: .certname, serial: .value}'
# or just for np-rcc hosts
pe-get-hosts boardserialnumber | jq '.[] | select( .certname | contains("np-rcc") ) | {host: .certname, serial: .value}'

# get a specific fact for all hosts
pe-get-hosts <factname>
# optionally with a specific value
pe-get-hosts <factname>/<value>
# eg to show all hosts that need a reboot due to apt updates
pe-get-hosts apt_reboot_required/true | jq '.[] | select(.environment == "melbourne") | {host: .certname}' | awk '/host/{print $2}' | sort
# show hosts with an "INTEL SSDSC2BX20" in sda
pe-get-hosts blockdevice_sda_model/INTEL%20SSDSC2BX20 | awk '/certname/{print $3}'

# get any changes in the latest report for a host (if there are any)
pe-get-host-changes <hostname>
