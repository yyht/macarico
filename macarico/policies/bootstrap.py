from __future__ import division

from macarico.policies.linear import LinearPolicy
from macarico import Policy
from macarico import util
import numpy as np
import dynet as dy


class BootstrapCost:
    def __init__(self, costs):
        self.costs = costs

    def npvalue(self):
        return dy.average(self.costs).npvalue()

    def __getitem__(self):
        assert(False)

# Sampling from Poisson with rate 1
def poisson_sample():
    temp = np.random.random()
    if(temp <= 0.3678794411714423215955):
        return 0
    if(temp <= 0.735758882342884643191):
        return 1
    if(temp <= 0.919698602928605803989):
        return 2
    if(temp <= 0.9810118431238461909214):
        return 3
    if(temp <= 0.9963401531726562876545):
        return 4
    if(temp <= 0.9994058151824183070012):
        return 5
    if(temp <= 0.9999167588507119768923):
        return 6
    if(temp <= 0.9999897508033253583053):
        return 7
    if(temp <= 0.9999988747974020309819):
        return 8
    if(temp <= 0.9999998885745216612793):
        return 9
    if(temp <= 0.9999999899522336243091):
        return 10
    if(temp <= 0.9999999991683892573118):
        return 11
    if(temp <= 0.9999999999364022267287):
        return 12
    if(temp <= 0.999999999995480147453):
        return 13
    if(temp <= 0.9999999999996999989333):
        return 14
    if(temp <= 0.9999999999999813223654):
        return 15
    if(temp <= 0.9999999999999989050799):
        return 16
    if(temp <= 0.9999999999999999393572):
        return 17
    if(temp <= 0.999999999999999996817):
        return 18
    if(temp <= 0.9999999999999999998412):
        return 19
    return 20


# Randomize over predictions from a base set of predictors
def bootstrap_probabilities(n_actions, policy_bag, state, deviate_to):
    preds = np.zeros(n_actions)
    bag_size = len(policy_bag)
    prob = 1. / bag_size
    for policy in policy_bag:
        a = policy(state, deviate_to)
        preds[a] += prob
    return preds


# Constructs a policy bag of linear policies, number of policies =
# len(features_bag)
def build_policy_bag(dy_model, features_bag, n_actions, loss_fn):
    return [LinearPolicy(dy_model, features, n_actions, loss_fn)
            for features in features_bag]


class BootstrapPolicy(Policy):
    """
        Bootstrapping policy
        TODO: how can we train this policy?
    """

    def __init__(self, dy_model, features_bag, n_actions, loss_fn='squared'):
        self.n_actions = n_actions
        self.bag_size = len(features_bag)
        self.policy_bag = build_policy_bag(dy_model, features_bag, n_actions,
                                           loss_fn)

    def __call__(self, state, deviate_to=None):
        action_probs = bootstrap_probabilities(self.n_actions, self.policy_bag,
                                               state, deviate_to)
        action, prob = util.sample_from_np_probs(action_probs)
        return action

    def predict_costs(self, state, deviate_to=None):
        all_costs = [policy.predict_costs(state, deviate_to)
                     for policy in self.policy_bag]
        return BootstrapCost(all_costs)

    def forward_partial_complete(self, all_costs, truth, actions):
        total_loss = None
        for policy, pred_costs in zip(self.policy_bag, all_costs):
            loss_i = policy.forward_partial_complete(pred_costs, truth, actions)
            count_i = poisson_sample()
            if total_loss is None:
                total_loss = count_i * loss_i
            else:
                total_loss = total_loss + count_i * loss_i
        return total_loss
