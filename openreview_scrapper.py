import argparse
import os
# from collections import defaultdict
from functools import partial
from dataclasses import dataclass

import openreview
import pandas as pd
from tqdm import tqdm


@dataclass(init=False)
class ICLRConference:
    decision_key: str
    group_id: str
    invitation_url: str

    def __init__(self, year: str):
        self.group_id = 'ICLR.cc'
        if year == '2018':
            self.invitation_url = f'{self.group_id}/{year}/Conference/-/Acceptance_Decision'
            self.decision_key = 'decision'
        elif year == '2019':
            # Because of the way the Program Chairs chose to run ICLR '19, there are no "decision notes";
            # instead, decisions are taken directly from Meta Reviews.
            self.invitation_url = f'{self.group_id}/{year}/Conference/-/Paper.*/Meta_Review'
            self.decision_key = 'recommendation'
        elif year >= '2020':
            self.invitation_url = f'{self.group_id}/{year}/Conference/Paper.*/-/Decision'
            self.decision_key = 'decision'
        else:
            self.invitation_url = ''
            self.decision_key = ''


@dataclass(init=False)
class NeurIPSWorkshop:
    decision_key: str
    group_id: str
    invitation_url: str

    def __init__(self, client: openreview.Client, year: str):
        self.group_id = 'NeurIPS.cc'
        invitations = openreview.tools.get_submission_invitations(client)
        self.submission_urls = [c for c in invitations if c.startswith(f'{self.group_id}/{year}/Workshop/')]
        self.invitation_urls = [c.replace('-/Blind_Submission', 'Paper.*/-/Decision') for c in self.submission_urls]
        self.decision_key = 'decision'


def download_conference_info(client: openreview.Client, conference: str, year: str, outdir: str = './', get_pdfs: bool = False):
    '''
    Main function for downloading conference metadata (and optionally, PDFs)
    forum here means the paper id
    '''

    print('Getting metadata')
    # get all submissions, reviews, and meta reviews, and organize them by forum ID
    # (a unique identifier for each paper; as in "discussion forum")
    if conference == 'iclr':
        conference_data = ICLRConference(year=year)

        submissions = openreview.tools.iterget_notes(
            client, invitation=f'{conference_data.group_id}/{year}/Conference/-/Blind_Submission')
        submissions_by_forum_id = {n.forum: n for n in submissions}

        # filter only accepted submissions' ids
        decision_info = openreview.tools.iterget_notes(
            client, invitation=conference_data.invitation_url)
        accepted_submissions_ids = {
            n.forum for n in decision_info if n.content[conference_data.decision_key] != 'Reject'}

    elif conference == 'neurips_workshop':
        conference_data = NeurIPSWorkshop(client=client, year=year)
        submissions_by_forum_id = {}
        accepted_submissions_ids = set()

        for submission_url, invitation_url in zip(conference_data.submission_urls, conference_data.invitation_urls):
            submissions = openreview.tools.iterget_notes(client, invitation=submission_url)
            submissions = {n.forum: n for n in submissions}
            submissions_by_forum_id = {**submissions, **submissions_by_forum_id}

            # filter only accepted submissions' ids
            decision_info = openreview.tools.iterget_notes(
                client, invitation=invitation_url)
            accepted_subs_ids = {
                n.forum for n in decision_info if n.content[conference_data.decision_key] != 'Reject'}
            accepted_submissions_ids = accepted_submissions_ids.union(accepted_subs_ids)

    # there should be 3 reviews per forum
    # reviews = openreview.tools.iterget_notes(
    #     client, invitation=f'{group_id}/{year}/Conference/-/Paper.*/Official_Review')
    # reviews_by_forum_id = defaultdict(list)
    # for review in reviews:
    #     reviews_by_forum_id[review.forum].append(review)

    # for every paper (forum), get the decision and the paper's content
    paper_info_df = pd.DataFrame(columns=['title', 'abstract_url', 'pdf_url'])
    abstracts_df = pd.DataFrame(columns=['title', 'abstract'])
    accepted_submissions = {}
    submissions_by_forum_id = {k: v for k, v in submissions_by_forum_id.items() if k in accepted_submissions_ids}

    for forum_id in submissions_by_forum_id:
        submission_content = submissions_by_forum_id[forum_id].content
        title = submission_content['title'].strip()
        abstract = submission_content['abstract']
        abstract = abstract.strip()
        abstract = ' '.join(abstract.split())

        paper_info_df = paper_info_df.append(
            {'title': title,
                'abstract_url': f'{forum_id}',
                'pdf_url': f'{forum_id}'},
            ignore_index=True)

        abstracts_df = abstracts_df.append(
            {'title': title,
                'abstract': repr(abstract)},
            ignore_index=True)

        accepted_submissions[forum_id] = submission_content['title']

    print('Writing tables to files')
    save_dir = os.path.join(outdir, f'{conference}', f'{year}')
    if not os.path.exists(save_dir):
        print(f'Creating folder {save_dir}')
        os.makedirs(save_dir)

    paper_info_df.to_csv(
        os.path.join(save_dir, 'paper_info.csv'), sep=';', index=False)

    abstracts_df.to_csv(
        os.path.join(save_dir, 'abstracts.csv'), sep='|', index=False)

    # if requested, download pdfs to a subdirectory.
    if get_pdfs:
        pdf_outdir = os.path.join(save_dir, 'papers')
        if not os.path.exists(pdf_outdir):
            print(f'Creating folder {pdf_outdir}')
            os.makedirs(pdf_outdir)

        print('Downloading pdf files')
        pbar = tqdm(accepted_submissions.items(), unit='pdf')
        for k, v in pbar:
            filename = f'{k}.pdf'
            pbar.set_description(filename)
            pdf_outfile = os.path.join(pdf_outdir, filename)
            if not os.path.exists(pdf_outfile):
                try:
                    pdf_binary = client.get_pdf(k)
                    with open(pdf_outfile, 'wb') as file_handle:
                        file_handle.write(pdf_binary)
                except:
                    print(
                        f'Error while trying to get pdf for {k}: {v}\n'
                        f'at https://openreview.net/pdf?id={k}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseurl', default='https://api.openreview.net')
    parser.add_argument('-c', '--conference', type=str, required=True,
                        choices=('iclr', 'neurips_workshop'),
                        help='conference to scrape data')
    parser.add_argument('-d', '--download_pdfs', default=False,
                        action='store_true', help='if included, download pdfs')
    parser.add_argument('-l', '--log_level', type=str, default='warning',
                        choices=('debug', 'info', 'warning',
                                 'error', 'critical', 'print'),
                        help='log level to debug')
    parser.add_argument('-o', '--outdir', default='data/',
                        help='directory where data should be saved')
    parser.add_argument('--password', default='',
                        help='defaults to empty string (guest user)')
    parser.add_argument('--username', default='',
                        help='defaults to empty string (guest user)')
    parser.add_argument('-y', '--year', type=str, required=True,
                        help='year of the conference')
    args = parser.parse_args()

    client = openreview.Client(
        baseurl=args.baseurl,
        username=args.username,
        password=args.password)

    download_conference_info(
        client, args.conference, args.year, args.outdir, get_pdfs=args.download_pdfs)
