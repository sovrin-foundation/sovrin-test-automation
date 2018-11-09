The chaossovtoken module is intended to provide python modules to test Sovrin
Token functionallity in context to exploratory (Chaos) experiments.

Sovrin Token is a plugin to Indy CLI and Indy Plenum, and therefore, extends
Hyperledger Indy functionality. All of the functionality provided in the
[chaosindy python module](https://github.com/hyperledger/indy-test-automation/chaos "chaosindy module location")
can be leveraged/reused in Sovrin Token experiments. Any features you consider
adding to chaossovtoken that are not token related should be added to chaosindy.
in the indy-test-automation repo. See the indy-test-automation Chaos[README](https://github.com/hyperledger/indy-test-automation/chaos/README.md "chaosindy README")
for further details.

# Development
At least one development environment useful for developing/vetting chaos
experiments is available in the [indy-test-automation repo](https://github.com/hyperledger/indy-test-automation/tree/master/environments/chaos)

If you opt to use the Vagrant + Virtualbox development environment, add the
following lines to [config.properties](https://github.com/ckochenower/indy-test-automation/blob/master/environments/chaos/config.properties.template)
before running `setup` or `vagrant up`:

```
# Sovrin Test Automation
repos.sovrin.test.automation.path=
repos.sovrin.test.automation.username=
repos.sovrin.test.automation.url=git@github.com:<USERNAME>/sovrin-test-automation.git
repos.sovrin.test.automation.branch=master
```

# Installation:
Follow the instructions in the
indy-test-automation Chaos [README](https://github.com/hyperledger/indy-test-automation/chaos/README.md "chaosindy README")
to install the chaosindy python module and then run

`env python3 setup.py develop`.
