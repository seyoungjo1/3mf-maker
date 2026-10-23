from pathlib import Path
import pickle,json,numpy as np,trimesh as tm
from trimesh.transformations import translation_matrix as T,rotation_matrix as R
O=Path(__file__).resolve().parent.parent
p=pickle.load(open(O/'AS/reference_R21_parts.pkl','rb'));source=pickle.load(open(O/'AS/reference_R18_parts.pkl','rb'))
limit=tm.creation.cylinder(radius=34.6,height=14.8,sections=192);limit.apply_translation([0,0,242.4])
hat=tm.boolean.intersection([source['drawer'],limit],engine='manifold');hat.apply_transform(T([0,0,259.8])@R(np.pi,[0,1,0]))
p['drawer']=tm.boolean.union([p['drawer'],hat],engine='manifold')
assert all(m.is_volume and len(m.split())==1 for m in p.values())
pickle.dump({n:m.copy(include_cache=False) for n,m in p.items()},open(O/'parts_nominal.pkl','wb'))
params=json.load(open(O/'AS/keyring_parameters.json'));params.update(rear_shape='Open semicircular boat ending; unchanged from R21',front_hat_shape='Full circular original hat; upper half restored',front_hat_source='Original R18 rear235..249.8 mirrored at259.8 without removing upper half')
json.dump(params,open(O/'AS/keyring_parameters.json','w'),indent=2)
features=pickle.load(open(O/'AS/changed_features.pkl','rb'));features['front_hat']=hat.copy(include_cache=False);pickle.dump(features,open(O/'AS/changed_features.pkl','wb'))
print([(n,len(m.faces),m.is_volume) for n,m in p.items()],flush=True)
