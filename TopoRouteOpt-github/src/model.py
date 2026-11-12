import torch.nn as nn
import torch.nn.functional as F

class TopoRouteOptNeuralNetwork(nn.Module):
    def __init__(self, input_dim, output_dim, hidden_dim, hidden_layer):
        super(TopoRouteOptNeuralNetwork, self).__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.hidden_dim = hidden_dim
        self.hidden_layer = hidden_layer

        layers = []
        layers.append(nn.Linear(input_dim, hidden_dim))
        layers.append(nn.ReLU())
        
        for _ in range(hidden_layer - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.ReLU())
        
        layers.append(nn.Linear(hidden_dim, output_dim))
        layers.append(nn.Sigmoid())  # Use Sigmoid for output layer to ensure outputs are in [0, 1]
        
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        """
        Forward pass of the neural network.
        
        Args:
            x (torch.Tensor): Input tensor of shape [batch_size, input_dim].
        
        Returns:
            torch.Tensor: Output tensor of shape [batch_size, output_dim].
        """
        return self.network(x)