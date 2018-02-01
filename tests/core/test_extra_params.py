# -*- coding: utf-8 -*-

from nose.tools import assert_equal

from openfisca_core import periods
from openfisca_core.periods import MONTH
from openfisca_core.variables import Variable
from openfisca_country_template import CountryTaxBenefitSystem
from openfisca_country_template.entities import Person
from openfisca_core.tools import assert_near
from openfisca_core.base_functions import requested_period_last_value


class formula_1(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(self, simulation, period):
        return simulation.calculate('formula_3', period, extra_params = [0])


class formula_2(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(self, simulation, period):
        return simulation.calculate('formula_3', period, extra_params = [1])


class formula_3(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(self, simulation, period, choice):
        return self.zeros() + choice


class formula_4(Variable):
    value_type = bool
    entity = Person
    base_function = requested_period_last_value
    definition_period = MONTH

    def formula(self, simulation, period, choice):
        return self.zeros() + choice


# TaxBenefitSystem instance declared after formulas
tax_benefit_system = CountryTaxBenefitSystem()
tax_benefit_system.add_variables(formula_1, formula_2, formula_3, formula_4)

reference_period = periods.period(u'2013-01')


def get_simulation():
    return tax_benefit_system.new_scenario().init_from_attributes(
        period = reference_period.first_month,
        ).new_simulation()


def test_cache():
    simulation = get_simulation()
    formula_1_result = simulation.calculate('formula_1', period = reference_period)
    formula_2_result = simulation.calculate('formula_2', period = reference_period)
    assert_near(formula_1_result, [0])
    assert_near(formula_2_result, [1])


def test_get_extra_param_names():
    simulation = get_simulation()
    formula_3_holder = simulation.person.get_holder('formula_3')
    assert formula_3_holder.get_extra_param_names(reference_period) == ('choice',)


def test_json_conversion():
    simulation = get_simulation()
    simulation.calculate('formula_1', period = reference_period)
    simulation.calculate('formula_2', period = reference_period)
    formula_3_holder = simulation.person.get_holder('formula_3')
    assert_equal(
        str(formula_3_holder.to_value_json()),
        "{'2013-01': {'{choice: 1}': [1], '{choice: 0}': [0]}}"
        )


def test_base_functions():
    simulation = get_simulation()
    assert simulation.calculate('formula_4', '2013-01', extra_params = [0]) == 0
    assert simulation.calculate('formula_4', '2013-01', extra_params = [1]) == 1

    # With the 'requested_period_last_value' base_function,
    # the value on an month can be infered from the year value, without running the function for that month
    assert simulation.calculate('formula_4', "2013-04", extra_params = [1]) == 1
