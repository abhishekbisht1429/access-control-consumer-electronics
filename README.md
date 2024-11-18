# Adversarial Attacks Resilient Machine Learning-Enabled Access Control Scheme for Consumer Electronics in IoT-Based Applications

## Instructions to run the test-bed setup

1. Run the cloud server using the command `python cloud_server.py` in a shell. The cloud server will start listening at localhost and port 8000 by default.
2. Run the gateway node using the command `python gateway_node.py` in a second shell. The gateway node will start listening at localhost and port 7000 by default.
3. Finally, run the smart device using the command `python smart_device.py` in a third shell. The smart device acts as a client that sends data to the gateway node using http requests.

## ML Training

- The directory `ml_training` contains an `ipynb` file which contains the details of training and demonstrates how adding poisson noise to it affects the results.
- It also contains the diabetes dataset used for training in the `hospital1.csv` file.