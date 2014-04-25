# -*- coding: utf-8 -*-

import os
import sys
import plac
import subprocess
import tempfile
from datetime import timedelta
from datetime import datetime
from jinja2 import Environment, PackageLoader
from pp.client.python.pdf import pdf        
import util


env = Environment(loader=PackageLoader('epxml', 'templates'))


@plac.annotations(
    xml_in=('Schedule XML file', 'option', 'i'),
    html_out=('Output HTML file', 'option', 'o'),
    pdf_converter=('Generate PDF output using prince or pdfreactor (princexml, remote-princexml, pdfreactor, remote-pdfreactor)', 'option', 'p')
    )
def conv(xml_in=None, html_out='brochure.html', pdf_converter=None):

    if not xml_in:
        raise ValueError('No XML input file specified (-i|--xml-in)')

    entries = list()
    for day in range(22, 25):
        date_str = '2014-07-{}'.format(day)
        entries.append(dict(entries=util.get_entries(xml_in, '//day[@date="{}"]/entry'.format(date_str)),
                            date_str=date_str))

    template = env.get_template('brochure.pt')
    html = template.render(
            day_entries=entries,
            view=util.JinjaView())
    with open(html_out, 'wb') as fp:
        print 'HTML output written to "{}"'.format(html_out)
        fp.write(html.encode('utf8'))

    if pdf_converter in ('princexml', 'pdfreactor'):
        # local pdf generation through PrinceXML or PDFreactor
        out_pdf = '{}.pdf'.format(os.path.splitext(html_out)[0])
        if pdf_converter == 'princexml':
            cmd = 'prince9 -v "{}" -o "{}"'.format(html_out, out_pdf)
        elif pdf_converter == 'pdfreactor':
            cmd = 'pdfreactor "{}" "{}"'.format(html_out, out_pdf)
        print 'Running: {}'.format(cmd)
        proc = subprocess.Popen(cmd, shell=True)
        status = proc.wait()
        print 'Exit code: {}'.format(status)
        if status != 0:
            raise RuntimeError('PDF generation failed')
        print 'PDF written to "{}"'.format(out_pdf)

    elif pdf_converter in ('remote-princexml', 'remote-pdfreactor'):
        # remote pdf generation through PrinceXML or PDFreactor
        # through https://pp-server.zopyx.com

        tmpd = tempfile.mkdtemp()
        html_filename  = os.path.join(tmpd, 'index.html')
        with open(html_filename, 'wb') as fp:
            fp.write(html.encode('utf-8'))

        server_url = os.environ['PP_SERVER_URL']
        authorization_token = os.environ['PP_AUTHORIZATION_TOKEN']
        output_filename = tempfile.mktemp(suffix='.pdf', dir=tmpd)
        result = pdf(source_directory=tmpd,
                     converter=pdf_converter.replace('remote-', ''),
                     output=output_filename,
                     server_url=server_url,
                     authorization_token=authorization_token,
                     verbose=True)

        if result['status'] != 'OK':
            raise RuntimeError('Remote PDF generation failed')

        print 'PDF written to "{}"'.format(result['output_filename'])
        return result['output_filename']


def main():
    plac.call(conv)


if __name__ == '__main__':
    main()