"""GT-free inference for the released Tree-LNDP matcher.

Geometry preparation follows the GPLv3 heiDATA release, DeformationPyramid
351cc74a5aa27783f88c49512210991902db32ea, without its training-label assembly.
This experimental integration is GPLv3; the original networks are imported.
"""
import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

import numpy as np
import torch
import yaml
from easydict import EasyDict

from windreg.benchmark import file_sha256, save_json
from windreg.metrics import xyz


def geometry(source, target, config, limits):
    from cpp_wrappers.cpp_subsampling import grid_subsampling
    from cpp_wrappers.cpp_neighbors import radius_neighbors
    points = torch.from_numpy(np.concatenate([source, target]).astype(np.float32))
    lengths = torch.tensor([len(source), len(target)], dtype=torch.int32)
    result = {key: [] for key in ('points', 'neighbors', 'pools', 'upsamples', 'stack_lengths')}
    result['features'] = torch.ones((len(points), 1), dtype=torch.float32)
    radius = config.first_subsampling_dl * config.conv_radius
    blocks, layer = [], 0

    def neighbors(query, support, qlen, slen, r):
        indices = radius_neighbors.batch_query(query, support, qlen, slen, radius=r)
        return torch.from_numpy(indices[:, :limits[layer]]).long()

    for i, block in enumerate(config.architecture):
        if 'global' in block or 'upsample' in block:
            break
        if not ('pool' in block or 'strided' in block):
            blocks.append(block)
            if i < len(config.architecture)-1 and 'upsample' not in config.architecture[i+1]:
                continue
        r = radius * config.deform_radius/config.conv_radius if any('deformable' in b for b in blocks[:-1]) else radius
        conv = neighbors(points, points, lengths, lengths, r) if blocks else torch.zeros((0,1),dtype=torch.int64)
        if 'pool' in block or 'strided' in block:
            p, n = grid_subsampling.subsample_batch(points, lengths, sampleDl=2*radius/config.conv_radius)
            pool_points, pool_lengths = torch.from_numpy(p), torch.from_numpy(n)
            r = radius * config.deform_radius/config.conv_radius if 'deformable' in block else radius
            pool = neighbors(pool_points, points, pool_lengths, lengths, r)
            up = neighbors(points, pool_points, lengths, pool_lengths, 2*r)
        else:
            pool = up = torch.zeros((0,1),dtype=torch.int64)
            pool_points, pool_lengths = torch.zeros((0,3)), torch.zeros(0,dtype=torch.int32)
        for name, value in zip(('points','neighbors','pools','upsamples','stack_lengths'),(points,conv,pool,up,lengths)):
            result[name].append(value)
        points, lengths = pool_points, pool_lengths
        radius, layer, blocks = radius*2, layer+1, []
    ns, nt = [int(n) for n in result['stack_lengths'][config.coarse_level]]
    result.update(src_mask=torch.ones((1,ns),dtype=torch.bool), tgt_mask=torch.ones((1,nt),dtype=torch.bool),
                  src_ind_coarse_split=torch.arange(ns), tgt_ind_coarse_split=torch.arange(nt),
                  src_ind_coarse=torch.arange(ns), tgt_ind_coarse=torch.arange(nt)+ns)
    return result


class AuthorMatcher:
    def __init__(self, author_source, weights, limits, device='cuda'):
        author = Path(author_source).resolve()/'correspondence'
        sys.path.insert(0, str(author))
        from lepard.pipeline import Pipeline
        from outlier_rejection.pipeline import Outlier_Rejection
        np.random.seed(0)
        torch.manual_seed(0)
        self.device = torch.device(device)
        config = EasyDict(yaml.safe_load((author/'configs/lepard.yaml').read_text()))
        reject_config = EasyDict(yaml.safe_load((author/'configs/outlier_rejection.yaml').read_text())['model'])
        self.matcher = Pipeline(config).to(device).eval()
        self.rejector = Outlier_Rejection(reject_config).to(device).eval()
        for model, name in [(self.matcher,'plants_S5_stems_weights.pth'),(self.rejector,'outlier_S5_stems_weights.pth')]:
            state = torch.load(Path(weights)/name,map_location='cpu',weights_only=True)
            model.load_state_dict(state['state_dict'],strict=True)
        self.config = config.kpfcn_config
        if len(limits) != self.config.num_layers or any(type(n) is not int or n <= 0 for n in limits):
            raise ValueError('One positive integer neighbor limit is required per KPConv layer')
        self.limits = limits

    def calibrate(self, pairs):
        bins = int(np.ceil(4/3*np.pi*(self.config.deform_radius+1)**3))
        hist = np.zeros((self.config.num_layers,bins),dtype=np.int64)
        for count, (source,target) in enumerate(pairs,1):
            data = geometry(source,target,self.config,[bins]*self.config.num_layers)
            for layer, matrix in enumerate(data['neighbors']):
                n = (matrix < matrix.shape[0]).sum(dim=1).numpy()
                hist[layer] += np.bincount(n,minlength=bins)[:bins]
            if hist.sum(axis=1).min() > 2000:
                break
        cumulative = np.cumsum(hist.T,axis=0)
        self.limits = np.sum(cumulative < .8*cumulative[-1],axis=0).tolist()
        return {'neighborhood_limits':self.limits,'calibration_pairs':count,'points_per_layer':hist.sum(axis=1).tolist()}

    def predict(self, source, target):
        started = perf_counter()
        source,target = xyz(source),xyz(target)
        # Match the released dataset's shared float32 centering.
        source, target = source.astype(np.float32),target.astype(np.float32)
        center = np.vstack([source,target]).mean(axis=0,keepdims=True)
        data = geometry(source-center,target-center,self.config,self.limits)
        data = {k:[x.to(self.device) for x in v] if isinstance(v,list) else v.to(self.device) for k,v in data.items()}
        with torch.no_grad():
            data = self.matcher(data)
            confidence = self.rejector(data)[0]
            pairs = data['vec_6d'][0]
            result = {'source':pairs[:,:3].cpu().numpy()+center,
                      'target':pairs[:,3:].cpu().numpy()+center,
                      'confidence':confidence.cpu().numpy()}
        return result, {'runtime_s':perf_counter()-started,'matches':len(pairs),
                        'accepted_matches':int((result['confidence']>.4).sum())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--author-source', required=True, type=Path)
    parser.add_argument('--weights', required=True, type=Path)
    parser.add_argument('--calibration', required=True, type=Path)
    parser.add_argument('--device', default='cuda')
    commands = parser.add_subparsers(dest='command', required=True)
    batch = commands.add_parser('batch')
    batch.add_argument('manifest', type=Path)
    batch.add_argument('destination', type=Path)
    pair = commands.add_parser('pair')
    pair.add_argument('source', type=Path)
    pair.add_argument('target', type=Path)
    pair.add_argument('destination', type=Path)
    args = parser.parse_args()
    args.destination.mkdir(parents=True,exist_ok=False)
    calibration = json.loads(args.calibration.read_text())
    save_json(args.destination/'calibration.json', calibration)
    save_json(args.destination/'provenance.json', {
        'integration_sha256': file_sha256(__file__),
        'author_code_sha256': {str(p.relative_to(args.author_source)): file_sha256(p)
                              for p in sorted(args.author_source.rglob('*.py'))},
        'weights_sha256': {name: file_sha256(args.weights/name) for name in
                          ('plants_S5_stems_weights.pth', 'outlier_S5_stems_weights.pth')},
        'calibration_sha256': file_sha256(args.calibration), 'device': args.device,
        'torch': torch.__version__, 'numpy': np.__version__,
        'input_manifest_sha256': file_sha256(args.manifest) if args.command == 'batch' else None,
        'failure_policy': 'Record every case. No automatic retry. Nonzero exit if any fail.'})
    matcher = AuthorMatcher(args.author_source, args.weights, calibration['neighborhood_limits'], args.device)
    if args.command == 'batch':
        cases = json.loads(args.manifest.read_text())['cases']
        root = args.manifest.parent
    else:
        cases = [{'id':'anchors', 'source':str(args.source.resolve()), 'target':str(args.target.resolve())}]
        root = Path('.')
    ids = [case['id'] for case in cases]
    if not ids or len(set(ids)) != len(ids) or any(Path(n).name != n or n in {'.','..',''} for n in ids):
        raise ValueError('Case IDs must be unique simple filenames')
    records = []
    for case in cases:
        record = {'id':case['id'], 'status':'failed'}
        try:
            paths = [root/case[key] for key in ('source','target')]
            record['input_sha256'] = {key:file_sha256(path) for key,path in zip(('source','target'),paths)}
            source,target = [np.load(path,allow_pickle=False) for path in paths]
            prediction,info = matcher.predict(source,target)
            np.savez(args.destination/(case['id']+'.npz'),**prediction)
            record.update(status='complete',**info)
        except Exception as error:
            record['error'] = type(error).__name__+': '+str(error)
        records.append(record)
        save_json(args.destination/'cases.json', records)
        print(json.dumps(record),flush=True)
    if any(r['status'] != 'complete' for r in records):
        raise SystemExit(1)
