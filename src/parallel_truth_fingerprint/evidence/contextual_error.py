"""Orthogonal reconstruction-error components for paired physical/supervisory inputs."""


def components(observed, reconstructed):
    import numpy as np
    x,y=np.asarray(observed,dtype='float32'),np.asarray(reconstructed,dtype='float32')
    if x.shape!=y.shape or x.ndim!=3 or x.shape[1:]!=(2,8):
        raise ValueError('Expected matching tensors shaped (N,2,8).')
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Non-finite input or reconstruction.')
    ep=y[:,:,:4]-x[:,:,:4]
    es=y[:,:,4:]-x[:,:,4:]
    common=np.mean(((ep+es)/2)**2,axis=(1,2))
    relational=np.mean(((ep-es)/2)**2,axis=(1,2))
    total=np.mean((x-y)**2,axis=(1,2))
    if not np.allclose(total,common+relational,rtol=1e-5,atol=1e-8):
        raise ValueError('Error decomposition identity failed.')
    direct=np.mean(((x[:,:,:4]-x[:,:,4:])/2)**2,axis=(1,2))
    return {'global_mse':total,'common_error':common,'relational_error':relational,'direct_gap':direct}
