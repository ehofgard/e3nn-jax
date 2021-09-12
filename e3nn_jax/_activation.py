import jax
import jax.numpy as jnp

from e3nn_jax import Irreps


def normalize_act(phi):
    with jax.core.eval_context():
        k = jax.random.PRNGKey(0)
        x = jax.random.normal(k, (1_000_000,))
        c = jnp.mean(phi(x)**2)**0.5

        def rho(x):
            return phi(x) / c
        return rho


def parity_act(phi):
    with jax.core.eval_context():
        x = jnp.linspace(0.0, 10.0, 256)

        a1, a2 = phi(x), phi(-x)
        if jnp.max(jnp.abs(a1 - a2)) < 1e-5:
            return 1
        elif jnp.max(jnp.abs(a1 + a2)) < 1e-5:
            return -1
        else:
            return 0


class Activation:
    irreps_in: Irreps
    irreps_out: Irreps

    def __init__(self, irreps_in, acts):
        irreps_in = Irreps(irreps_in)
        assert len(irreps_in) == len(acts), (irreps_in, acts)

        irreps_out = []
        for (mul, (l_in, p_in)), act in zip(irreps_in, acts):
            if act is not None:
                if l_in != 0:
                    raise ValueError("Activation: cannot apply an activation function to a non-scalar input.")

                p_out = parity_act(act) if p_in == -1 else p_in
                irreps_out.append((mul, (0, p_out)))

                if p_out == 0:
                    raise ValueError("Activation: the parity is violated! The input scalar is odd but the activation is neither even nor odd.")
            else:
                irreps_out.append((mul, (l_in, p_in)))

        # normalize the second moment
        acts = [normalize_act(act) if act is not None else None for act in acts]

        self.irreps_in = irreps_in
        self.irreps_out = Irreps(irreps_out)
        self.acts = acts

    def __call__(self, features):
        assert isinstance(features, list)
        return [x if act is None else act(x) for act, x in zip(self.acts, features)]
