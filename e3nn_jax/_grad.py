from typing import Callable, List

import jax
import jax.numpy as jnp

import e3nn_jax as e3nn
from e3nn_jax.util import prod


def grad(
    fun: Callable[[e3nn.IrrepsArray], e3nn.IrrepsArray],
) -> e3nn.IrrepsArray:
    r"""Gradient of an equivariant function.

    Examples:
        >>> f = grad(lambda x: x)
        >>> x = e3nn.IrrepsArray("1o", jnp.array([1.0, 2, 3]))
        >>> f(x).irreps
        0e+1e+2e
    """

    def _grad(x: e3nn.IrrepsArray) -> e3nn.IrrepsArray:
        irreps_in = x.irreps
        leading_shape_in = x.shape[:-1]

        def naked_fun(x_list: List[jnp.ndarray]) -> List[jnp.ndarray]:
            x_ = e3nn.IrrepsArray.from_list(irreps_in, x_list, leading_shape_in)
            y = fun(x_)
            return y.list, (y.irreps, y.shape[:-1])

        jac, (irreps_out, leading_shape_out) = jax.jacobian(naked_fun, has_aux=True)(x.list)

        irreps = []
        list = []
        for mir_out, y_list in zip(irreps_out, jac):
            for mir_in, z in zip(irreps_in, y_list):
                assert z.shape == (
                    leading_shape_out + (mir_out.mul, mir_out.ir.dim) + leading_shape_in + (mir_in.mul, mir_in.ir.dim)
                )
                z = jnp.reshape(
                    z,
                    (prod(leading_shape_out), mir_out.mul, mir_out.ir.dim, prod(leading_shape_in), mir_in.mul, mir_in.ir.dim),
                )
                for ir in mir_out.ir * mir_in.ir:
                    irreps.append((mir_out.mul * mir_in.mul, ir))
                    list.append(
                        jnp.einsum(
                            "auibvj,ijk->abuvk", z, jnp.sqrt(ir.dim) * e3nn.clebsch_gordan(mir_out.ir.l, mir_in.ir.l, ir.l)
                        ).reshape(leading_shape_out + leading_shape_in + (mir_out.mul * mir_in.mul, ir.dim))
                    )
        return e3nn.IrrepsArray.from_list(irreps, list, leading_shape_out + leading_shape_in)

    return _grad