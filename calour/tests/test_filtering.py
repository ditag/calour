# ----------------------------------------------------------------------------
# Copyright (c) 2016--,  Calour development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

from unittest import main

from numpy.testing import assert_array_equal
import numpy as np

from calour._testing import Tests, assert_experiment_equal
from calour.filtering import _balanced_subsample
import calour as ca


class FilteringTests(Tests):
    def setUp(self):
        super().setUp()
        self.test2 = ca.read(self.test2_biom, self.test2_samp, self.test2_feat, normalize=None)
        self.test1 = ca.read(self.test1_biom, self.test1_samp, self.test1_feat, normalize=None)

    def test_balanced_subsample(self):
        rand = np.random.RandomState(None)
        d = rand.choice([0, 1, 2], 9)
        for n in (1, 3, 6, 9, 10):
            keep = _balanced_subsample(d, n, None)
            d2 = d[keep]
            uniq, counts = np.unique(d2, return_counts=True)
            self.assertTrue(np.all(counts == n))

    def test_downsample_sample(self):
        obs = self.test2.downsample('group')
        # should be down to 4 samples; feature number is the same
        self.assertEqual(obs.shape, (4, 8))

        sid = obs.sample_metadata.index.tolist()
        all_sid = self.test2.sample_metadata.index.tolist()
        exp = self.test2.reorder([all_sid.index(i) for i in sid])
        assert_experiment_equal(obs, exp)

    def test_downsample_feature(self):
        obs = self.test2.downsample('oxygen', axis=1)
        sid = obs.feature_metadata.index.tolist()
        self.assertEqual(obs.shape, (9, 4))

        all_sid = self.test2.feature_metadata.index.tolist()
        exp = self.test2.reorder([all_sid.index(i) for i in sid], axis=1)
        self.assertEqual(obs, exp)

    def test_downsample_num_keep(self):
        # test keeping num_keep samples, and inplace
        obs = self.test1.downsample('group', num_keep=9, inplace=True)
        # should be down to 2 groups (18 samples); feature number is the same
        self.assertEqual(obs.shape, (18, 12))
        self.assertEqual(set(obs.sample_metadata['group']), set(['1', '2']))
        self.assertIs(obs, self.test1)

    def test_filter_by_metadata_sample_edge_cases(self):
        # no group 3 - none filtered
        obs = self.test2.filter_by_metadata('group', [3])
        self.assertEqual(obs.shape, (0, 8))
        obs = self.test2.filter_by_metadata('group', [3], negate=True)
        assert_experiment_equal(obs, self.test2)

        # all samples are filtered
        obs = self.test2.filter_by_metadata('group', [1, 2])
        assert_experiment_equal(obs, self.test2)
        obs = self.test2.filter_by_metadata('group', [1, 2], negate=True)
        self.assertEqual(obs.shape, (0, 8))

    def test_filter_by_metadata_sample(self):
        for sparse, inplace in [(True, False), (True, True), (False, False), (False, True)]:
            test2 = ca.read(self.test2_biom, self.test2_samp, self.test2_feat,
                            sparse=sparse, normalize=None)
            # only filter samples bewtween 3 and 7.
            obs = test2.filter_by_metadata(
                'ori.order', lambda l: [7 > i > 3 for i in l], inplace=inplace)
            self.assertEqual(obs.shape, (3, 8))
            self.assertEqual(obs.sample_metadata.index.tolist(), ['S5', 'S6', 'S7'])
            if inplace:
                self.assertIs(obs, test2)
            else:
                self.assertIsNot(obs, test2)

    def test_filter_by_metadata_feature_edge_cases(self):
        # none filtered
        obs = self.test2.filter_by_metadata('oxygen', ['facultative'], axis=1)
        self.assertEqual(obs.shape, (9, 0))
        obs = self.test2.filter_by_metadata('oxygen', ['facultative'], axis=1, negate=True)
        assert_experiment_equal(obs, self.test2)

    def test_filter_by_metadata_feature(self):
        for sparse, inplace in [(True, False), (True, True), (False, False), (False, True)]:
            test2 = ca.read(self.test2_biom, self.test2_samp, self.test2_feat, sparse=sparse, normalize=None)
            # only filter samples with id bewtween 3 and 7.
            obs = test2.filter_by_metadata('oxygen', ['anaerobic'], axis=1, inplace=inplace)
            self.assertEqual(obs.shape, (9, 2))
            self.assertListEqual(obs.feature_metadata.index.tolist(), ['TG', 'TC'])
            if inplace:
                self.assertIs(obs, test2)
            else:
                self.assertIsNot(obs, test2)

    def test_filter_by_metadata_na(self):
        test = self.test2 = ca.read(self.test2_biom, self.test2_samp, self.test2_feat,
                                    normalize=None, feature_metadata_kwargs={'na_values': 'B'})
        test_drop = test.filter_by_metadata('level1', select=None, axis='f')
        self.assertEqual(self.test2.sample_metadata.index.tolist(),
                         test_drop.sample_metadata.index.tolist())
        self.assertEqual(['AT', 'AG', 'AC', 'TA', 'TT', 'TC'],
                         test_drop.feature_metadata.index.tolist())

    def test_filter_by_data_sample_edge_cases(self):
        # all samples are filtered out
        obs = self.test2.filter_by_data('abundance', axis=0, cutoff=100000, mean_or_sum='sum')
        self.assertEqual(obs.shape, (0, 8))
        # none is filtered out
        obs = self.test2.filter_by_data('abundance', axis=0, cutoff=1, mean_or_sum='sum')
        assert_experiment_equal(obs, self.test2)
        self.assertIsNot(obs, self.test2)

    def test_filter_by_data_sample(self):
        for sparse, inplace in [(True, False), (True, True), (False, False), (False, True)]:
            test2 = ca.read(self.test2_biom, self.test2_samp, self.test2_feat, sparse=sparse, normalize=None)
            # filter out samples with abundance < 1200. only the last sample is filtered out.
            obs = test2.filter_by_data('abundance', axis=0, inplace=inplace, cutoff=1200, mean_or_sum='sum')
            self.assertEqual(obs.shape, (8, 8))
            self.assertNotIn('S9', obs.sample_metadata)
            for sid in obs.sample_metadata.index:
                assert_array_equal(obs[sid, :], self.test2[sid, :])

            if inplace:
                self.assertIs(obs, test2)
            else:
                self.assertIsNot(obs, test2)

    def test_filter_by_data_feature_edge_cases(self):
        # all features are filtered out
        obs = self.test2.filter_by_data('abundance', axis=1, cutoff=10000, mean_or_sum='sum')
        self.assertEqual(obs.shape, (9, 0))

        # none is filtered out
        obs = self.test2.filter_by_data('abundance', axis=1, cutoff=1, mean_or_sum='sum')
        assert_experiment_equal(obs, self.test2)
        self.assertIsNot(obs, self.test2)

    def test_filter_by_data_feature(self):
        # one feature is filtered out when cutoff is set to 25
        for inplace in [True, False]:
            obs = self.test2.filter_by_data('abundance', axis=1, inplace=inplace, cutoff=25, mean_or_sum='sum')
            self.assertEqual(obs.shape, (9, 7))
            self.assertNotIn('TA', obs.feature_metadata)
            for fid in obs.feature_metadata.index:
                assert_array_equal(obs[:, fid], self.test2[:, fid])
            if inplace:
                self.assertIs(obs, self.test2)
            else:
                self.assertIsNot(obs, self.test2)

    def test_filter_prevalence(self):
        # this should filter all features because the upper limit is 100%
        exp = self.test1.filter_prevalence(fraction=0.5)
        fids = ['AA', 'AT', 'AG', 'TA', 'TT', 'TG', 'TC', 'GG']
        self.assertListEqual(exp.feature_metadata.index.tolist(), fids)
        self.assertEqual(exp.shape[0], self.test1.shape[0])

    def test_filter_prevalence_zero(self):
        # keep only features present at least in 0.5 the samples
        exp = self.test1.filter_prevalence(fraction=1.01)
        self.assertListEqual(exp.feature_metadata.index.tolist(), [])
        self.assertEqual(exp.shape[0], self.test1.shape[0])

    def test_filter_prevalence_check(self):
        # filter over all samples always filter more or euqal features than
        # filter over sample groups
        frac = 0.001
        exp = self.test1.filter_prevalence(fraction=frac)
        n = exp.shape[1]
        for i in self.test1.sample_metadata.columns:
            x = self.test1.filter_prevalence(fraction=frac, field=i)
            self.assertLessEqual(x.shape[1], n)

    def test_filter_abundance(self):
        exp = self.test1.filter_abundance(17008)
        self.assertEqual(exp.shape[1], 2)
        fids = ['TC', 'GG']
        self.assertListEqual(exp.feature_metadata.index.tolist(), fids)

    def test_filter_mean_abundance(self):
        # default is 0.01 - keep features with mean abundance >= 1%
        test1 = self.test1.normalize()

        exp = test1.filter_mean_abundance()
        fids = ['AT', 'TG', 'TC', 'GG']
        self.assertListEqual(exp.feature_metadata.index.tolist(), fids)
        self.assertEqual(exp.shape[0], self.test1.shape[0])

        exp = test1.filter_mean_abundance(0.4, field=None)
        fids = ['TC', 'GG']
        self.assertListEqual(exp.feature_metadata.index.tolist(), fids)

        exp = test1.filter_mean_abundance(0.6, field=None)
        self.assertListEqual(exp.feature_metadata.index.tolist(), [])

        exp = test1.filter_mean_abundance(0.6, field='group')
        fids = ['GG']
        self.assertListEqual(exp.feature_metadata.index.tolist(), fids)

    def test_filter_mean_abundance_check(self):
        # filter over all samples always filter more or euqal features than
        # filter over sample groups
        abund = 0.001
        exp = self.test1.filter_mean_abundance(abund)
        n = exp.shape[1]
        for i in self.test1.sample_metadata.columns:
            x = self.test1.filter_mean_abundance(abund, field=i)
            self.assertLessEqual(x.shape[1], n)

    def test_filter_ids_not_in_list(self):
        fids = ['GG', 'pita']
        exp = self.test1.filter_ids(fids)
        self.assertListEqual(exp.feature_metadata.index.tolist(), ['GG'])

    def test_filter_ids_default(self):
        fids = ['GG', 'AA', 'TT']
        exp = self.test1.filter_ids(fids)
        self.assertListEqual(exp.feature_metadata.index.tolist(), fids)
        self.assertIsNot(exp, self.test1)

    def test_filter_ids_samples_inplace_negate(self):
        badsamples = ['S1', 'S3', 'S5', 'S7', 'S9', 'S11', 'S13', 'S15', 'S17', 'S19']
        oksamples = list(set(self.test1.sample_metadata.index.values).difference(set(badsamples)))
        exp = self.test1.filter_ids(badsamples, axis=0, negate=True, inplace=True)
        self.assertCountEqual(list(exp.sample_metadata.index.values), oksamples)
        self.assertIs(exp, self.test1)

    def test_filter_sample_categories(self):
        test = self.test1.filter_ids(['badsample'], axis=0, negate=True)
        # does not filter anything
        assert_experiment_equal(test.filter_sample_categories('group', 9), test)
        # filter group of 2
        assert_experiment_equal(test.filter_sample_categories('group', 10),
                                test.filter_samples('group', '1'))


if __name__ == '__main__':
    main()
