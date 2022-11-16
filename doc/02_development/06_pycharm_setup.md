# PyCharm Professional

For a seamless development experience, we recommend the use of [PyCharm Professional](https://www.jetbrains.com/pycharm/).

## Getting an education license

To use PyCharm Professional, you need a license.
Fortunately, all students of Uni-Augsburg can get a free education license using their @uni-a.de mail-address.

For this, follow the process on the Jetbrains website: [Request Education License](https://www.jetbrains.com/shop/eform/students).

After completing this process, you can continue to install PyCharm Professional

## Installing PyCharm professional

### Jetbrains Toolbox

The easiest way to install PyCharm Professional and keep it up to date, is to use [Jetbrains Toolbox](https://www.jetbrains.com/toolbox-app/).

For easy installation, there is a [convenience script](https://github.com/nagygergo/jetbrains-toolbox-install),
that downloads JetBrains toolbox and installs it to the right folder.

```shell
sudo curl -fsSL https://raw.githubusercontent.com/nagygergo/jetbrains-toolbox-install/master/jetbrains-toolbox.sh | bash
```

After this you can open the toolbox with the following command:

```shell
jetbrains-toolbox
```

The interface should open, and you can easily install _PyCharm Professional_.

### Setting up docker-compose standalone binary

To use the docker-compose integration of PyCharm Professional,
you additionally need to install the standalone version of [docker-compose](https://docs.docker.com/compose/install/other/)

```shell
# Download binary
sudo curl -SL https://github.com/docker/compose/releases/download/v2.12.2/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose

# Make binary executable
sudo chmod +x /usr/local/bin/docker-compose

# Create symbolic link to make the binary discoverable
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

```

### Setting up the paf22 project with docker-compose interpreter

After opening and activating PyCharm Professional with your education license, open the existing paf22 project-folder in PyCharm Professional.

The last step is to set up the docker-compose integration.
For this, please follow this [official guide](https://www.jetbrains.com/help/idea/configuring-remote-python-sdks.html#DockerCompose), while selecting `./build/docker-compose.yml` as configuration file and `agent` as service.

After the initial indexing, PyCharm will provide intelligent code feedback and refactoring options in Python.