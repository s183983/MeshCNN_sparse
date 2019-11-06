import torch
from torch.nn import ConstantPad2d
import numpy as np
from torch_sparse import spmm, transpose


def isin(ar1, ar2):
    return (ar1[..., None] == ar2).any(-1)


class MeshUnion:
    def __init__(self, n, device=torch.device('cpu')):
        self.__size = n
        self.rebuild_features = self.rebuild_features_average
        idxs = torch.arange(n, device=device)
        self.sparse_groups = torch.sparse.FloatTensor(torch.stack([idxs, idxs]), torch.ones(n, device=device)).to(device)
        #self.groups = torch.eye(n).to(device)

    def union(self, source, target):
        #if not self.sparse_groups.is_coalesced():
        #    self.sparse_groups = self.sparse_groups.coalesce()

        # All of this mess is just adding two rows
        # equivalent to self.groups[target, :] += self.groups[source, :]
        idxs = self.sparse_groups._indices()


        if type(source) in [np.int64, int] and type(target) in [np.int64, int]:

            source_mask = idxs[0,:] == source
            source_columns = idxs[1, source_mask]
            target_rows = torch.ones(source_mask.sum(), dtype=torch.int64, device=self.sparse_groups.device) * target
            source_target_idxs = torch.stack([target_rows, source_columns])

            values = self.sparse_groups._values()[source_mask]

            all_values = torch.cat([self.sparse_groups._values(), values], dim=0)
            all_idxs = torch.cat([self.sparse_groups._indices(), source_target_idxs], dim=1)
            self.sparse_groups = torch.sparse.FloatTensor(all_idxs, all_values)#.coalesce()

        elif type(source) == list and type(target) == list:
            idxs = idxs.cpu().numpy()
            source_mask = np.isin(idxs[0,:], source)
            source_columns = torch.from_numpy(idxs[1, source_mask])
            target_rows = torch.from_numpy(idxs[0,:][source_mask])
            source_target_idxs = torch.stack([target_rows, source_columns]).to(self.sparse_groups.device)

            values = self.sparse_groups._values()[source_mask]
            all_values = torch.cat([self.sparse_groups._values(), values], dim=0)
            all_idxs = torch.cat([self.sparse_groups._indices(), source_target_idxs], dim=1)
            self.sparse_groups = torch.sparse.FloatTensor(all_idxs, all_values).coalesce()

        else:
            raise ValueError()




    def remove_group(self, index):
        return

    def get_group(self, edge_key):
        return self.groups[edge_key, :]

    def get_occurrences(self):
        #return torch.sum(self.groups, 0)
        return torch.sparse.sum(self.sparse_groups, 0).to_dense()

    def get_groups(self, tensor_mask):
        #if not self.sparse_groups.is_coalesced():
        #    self.sparse_groups = self.sparse_groups.coalesce()

        where_mask = torch.from_numpy(np.argwhere(tensor_mask.numpy()).squeeze()).to("cuda")
        value_mask = isin(self.sparse_groups._indices()[0, :], where_mask)

        new_cols = self.sparse_groups._indices()[1,value_mask]
        # Rescale row_idx to slice
        temp = self.sparse_groups._indices()[0,value_mask]
        d = {j: i for i, j in enumerate(temp.unique().cpu().numpy())}
        new_rows = temp.cpu().apply_(lambda x: d[x]).to(self.sparse_groups.device)

        idxs = torch.stack([new_rows, new_cols])
        #self.groups = torch.clamp(self.groups, 0, 1)
        #return self.groups[tensor_mask, :]
        return torch.sparse.FloatTensor(idxs, self.sparse_groups._values()[value_mask], (tensor_mask.sum(), self.sparse_groups.shape[1]))

    def rebuild_features_average(self, features, mask, target_edges):
        self.prepare_groups(features, mask)


        if not self.sparse_groups.is_coalesced():
            self.sparse_groups = self.sparse_groups.coalesce()
        idxs, values = transpose(self.sparse_groups._indices(), self.sparse_groups._values(), self.sparse_groups.shape[0], self.sparse_groups.shape[1])
        fe = spmm(idxs, values, self.sparse_groups.shape[1], self.sparse_groups.shape[0], features.squeeze(-1).T).T

        # fe = torch.matmul(features.squeeze(-1), self.groups)
        #occurrences = torch.sum(self.groups, 0).expand(fe.shape)
        occurrences = torch.sparse.sum(self.sparse_groups, 0).to_dense().expand(fe.shape)
        fe = fe / occurrences
        padding_b = target_edges - fe.shape[1]
        if padding_b > 0:
            padding_b = ConstantPad2d((0, padding_b, 0, 0), 0)
            fe = padding_b(fe)
        return fe



    def prepare_groups(self, features, mask):
        #tensor_mask = torch.from_numpy(mask)
        #self.groups = torch.clamp(self.groups[tensor_mask, :], 0, 1).transpose_(1, 0)
        #padding_a = features.shape[1] - self.groups.shape[0]
        #if padding_a > 0:
        #    padding_a = ConstantPad2d((0, 0, 0, padding_a), 0)
        #    self.groups = padding_a(self.groups)

        #if not self.sparse_groups.is_coalesced():
        #    self.sparse_groups = self.sparse_groups.coalesce()
        where_mask = torch.from_numpy(np.argwhere(mask).squeeze()).to("cuda")
        value_mask = isin(self.sparse_groups._indices()[0,:], where_mask)

        values = self.sparse_groups._values()[value_mask]
        indicies = self.sparse_groups._indices()[:,value_mask]

        values = torch.clamp(values, 0, 1)

        new_cols = indicies[1,:]
        # Rescale row_idx to slice
        temp = indicies[0,:]
        d = {j: i for i, j in enumerate(temp.unique().cpu().numpy())}
        new_rows = temp.cpu().apply_(lambda x: d[x]).to(self.sparse_groups.device)

        indicies = torch.stack([new_rows, new_cols])

        from torch_sparse import transpose
        indicies, values = transpose(indicies, values, self.sparse_groups.shape[0], self.sparse_groups.shape[1])


        self.sparse_groups = torch.sparse.FloatTensor(indicies, values, (features.shape[1], mask.sum()))

