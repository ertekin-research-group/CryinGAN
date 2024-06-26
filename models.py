import torch.nn as nn
import torch


class Generator(nn.Module):
    def __init__(self, args, n_atoms_total):
        super(Generator, self).__init__()
        self.latent_dim = args.latent_dim
        self.gen_channels_1 = args.gen_channels_1
        self.n_atoms_total = n_atoms_total

        self.l1 = nn.Sequential(nn.Linear(self.latent_dim, self.gen_channels_1*self.n_atoms_total),nn.ReLU(True))
        self.map1 = nn.Sequential(nn.ConvTranspose2d(self.gen_channels_1,256,(1,3),stride = 1,padding=0),nn.BatchNorm2d(256,0.8),nn.ReLU(True))
        self.map2 = nn.Sequential(nn.ConvTranspose2d(256,512,(1,1),stride = 1,padding=0),nn.BatchNorm2d(512,0.8),nn.ReLU(True))
        self.map3 = nn.Sequential(nn.ConvTranspose2d(512,256,(1,1),stride = 1,padding=0),nn.BatchNorm2d(256,0.8),nn.ReLU(True)) 
        self.map4 = nn.Sequential(nn.ConvTranspose2d(256,1,(1,1),stride=1,padding=0)) 
        self.sigmoid = nn.Sigmoid()

    def forward(self, noise):
        gen_input = noise
        h = self.l1(gen_input)
        h = h.view(h.shape[0], self.gen_channels_1, self.n_atoms_total, 1)   # h.shape[0] is the current batch size 
        h = self.map1(h)
        h = self.map2(h)
        h = self.map3(h)
        h = self.map4(h)
        pos = self.sigmoid(h)
        
        return pos  # torch.Size is (current_batch_size, 1, n_atoms_total, 3)


class CoordinateDiscriminator(nn.Module):
    def __init__(self, args, n_atoms_elements):
        super(CoordinateDiscriminator, self).__init__()
        self.n_elements = len(n_atoms_elements)
        self.n_atoms_elements = n_atoms_elements
        
        self.model = nn.Sequential(nn.Conv2d(in_channels = 1, out_channels = 512, kernel_size = (1,3), stride = 1, padding = 0),nn.LeakyReLU(0.2, inplace=True),
                                   nn.Conv2d(in_channels = 512, out_channels = 512, kernel_size = (1,1), stride = 1, padding = 0),nn.LeakyReLU(0.2,inplace=True),
                                   nn.Conv2d(in_channels = 512, out_channels = 256, kernel_size= (1,1), stride = 1, padding = 0),nn.LeakyReLU(0.2,inplace=True))
        
        self.avgpool_elements = []
        for i in range(self.n_elements):
            self.avgpool_elements.append(nn.AvgPool2d(kernel_size = (self.n_atoms_elements[i],1)))

        self.feature_layer = nn.Sequential(nn.Linear(256*self.n_elements, 1000), nn.LeakyReLU(0.2, inplace =True), nn.Linear(1000,200),nn.LeakyReLU(0.2, inplace = True))
        self.output = nn.Sequential(nn.Linear(200,10))

    def forward(self, x):
        B = x.shape[0]
        output = self.model(x)
        
        output_elements = []   # Stores the output that has been sliced based on the element type
        start = 0
        for i in range(self.n_elements):
            stop = start + self.n_atoms_elements[i]
            output_slice = output[:,:,start:stop,:]
            output_slice = self.avgpool_elements[i](output_slice)
            output_elements.append(output_slice)
            start += self.n_atoms_elements[i]
        
        output_all = torch.cat(output_elements, dim=-2)
        output_all = output_all.view(B, -1)   # Flatten all channels

        feature = self.feature_layer(output_all)  # torch.Size is (current_batch_size, 200)
        return feature, self.output(feature)   # output(feature) has size (current_batch_size, 10)


class DistanceDiscriminator(nn.Module):
    def __init__(self, args, n_atoms_elements):
        super(DistanceDiscriminator, self).__init__()
        self.n_elements = len(n_atoms_elements)
        self.n_atoms_elements = n_atoms_elements
        self.n_neighbors = args.n_neighbors
        
        self.model = nn.Sequential(nn.Conv2d(in_channels = 1, out_channels = 512, kernel_size = (1,self.n_neighbors), stride = 1, padding = 0),nn.LeakyReLU(0.2, inplace=True),
                                   nn.Conv2d(in_channels = 512, out_channels = 512, kernel_size = (1,1), stride = 1, padding = 0),nn.LeakyReLU(0.2,inplace=True),
                                   nn.Conv2d(in_channels = 512, out_channels = 256, kernel_size= (1,1), stride = 1, padding = 0),nn.LeakyReLU(0.2,inplace=True))

        self.avgpool_elements = []
        for i in range(self.n_elements):
            self.avgpool_elements.append(nn.AvgPool2d(kernel_size = (self.n_atoms_elements[i],1)))

        self.feature_layer = nn.Sequential(nn.Linear(256*self.n_elements, 1000), nn.LeakyReLU(0.2, inplace =True), nn.Linear(1000,200),nn.LeakyReLU(0.2, inplace = True))
        self.output = nn.Sequential(nn.Linear(200,10))

    def forward(self, x):
        B = x.shape[0]
        output = self.model(x)

        output_elements = []   # Stores the output that has been sliced based on the element type
        start = 0
        for i in range(self.n_elements):
            stop = start + self.n_atoms_elements[i]
            output_slice = output[:,:,start:stop,:]
            output_slice = self.avgpool_elements[i](output_slice)
            output_elements.append(output_slice)
            start += self.n_atoms_elements[i]
        
        output_all = torch.cat(output_elements, dim=-2)
        output_all = output_all.view(B, -1)   # Flatten all channels

        feature = self.feature_layer(output_all)  # torch.Size is (current_batch_size, 200)
        return feature, self.output(feature)   # output(feature) has size (current_batch_size, 10)
        



